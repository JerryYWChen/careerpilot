from datetime import datetime, timezone
import logging
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from backend.models.analysis import CareerActionPlan, Gap, MatchStatus, PlannedAction
from backend.rag.acquisition import acquire_and_ingest_gap_source
from backend.rag.models import IngestionResult, IngestionStatus, RetrievalResult
from backend.rag.planning_context import retrieve_planning_context
from backend.rag.store import inspect_index
from backend.rag.web_models import (
    AcquisitionResult,
    AcquisitionStatus,
    FetchedWebPage,
    WebSearchResult,
)
from backend.services.planner_service import create_validated_career_action_plan


class FakeEmbeddingsEndpoint:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            data=[
                SimpleNamespace(index=index, embedding=[1.0, 0.0])
                for index, _ in enumerate(kwargs["input"])
            ]
        )


class FakeOpenAIClient:
    def __init__(self) -> None:
        self.embeddings = FakeEmbeddingsEndpoint()


class RecordingSearchProvider:
    def __init__(self) -> None:
        self.queries: list[tuple[str, int]] = []

    def search(self, query: str, *, limit: int) -> list[WebSearchResult]:
        self.queries.append((query, limit))
        return [
            WebSearchResult(
                title="Kubernetes Documentation",
                url="https://kubernetes.io/docs/concepts/overview/",
                snippet="Official Kubernetes concepts and getting started guidance.",
                rank=1,
                provider="test",
            )
        ]


class StaticPageFetcher:
    def fetch(self, source):
        return FetchedWebPage(
            requested_url=source.canonical_url,
            final_url=source.canonical_url,
            content_type="text/plain",
            encoding="utf-8",
            body=(
                b"Kubernetes coordinates containerized workloads across a cluster. "
                b"Start by deploying a small application, inspect its resources, "
                b"and practice updating and troubleshooting the deployment safely."
            ),
            fetched_at=datetime(2026, 9, 24, tzinfo=timezone.utc),
        )


def _gap(area: str = "Kubernetes") -> Gap:
    return Gap(
        area=area,
        status=MatchStatus.MISSING,
        evidence="PRIVATE RESUME EVIDENCE",
        reason="PRIVATE GAP REASON",
    )


def test_acquired_source_is_ingested_retrieved_and_added_to_planning_context(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "knowledge.db"
    embedding_client = FakeOpenAIClient()
    search_provider = RecordingSearchProvider()
    page_fetcher = StaticPageFetcher()
    acquisition_results: list[AcquisitionResult] = []

    def acquire(gap: Gap) -> AcquisitionResult:
        result = acquire_and_ingest_gap_source(
            gap,
            search_provider=search_provider,
            page_fetcher=page_fetcher,
            database_path=database_path,
            embedding_client=embedding_client,
        )
        acquisition_results.append(result)
        return result

    context = retrieve_planning_context(
        [_gap()],
        database_path=database_path,
        embedding_client=embedding_client,
        acquire_gap=acquire,
    )

    assert acquisition_results[0].status == AcquisitionStatus.INGESTED
    assert acquisition_results[0].ingestion_result is not None
    assert len(context) == 1
    assert context[0].document_title == "Kubernetes Documentation"
    assert "containerized workloads" in context[0].content

    documents, chunks = inspect_index(database_path)
    assert len(documents) == 1
    assert len(chunks) == 1
    assert documents[0]["source_url"] == (
        "https://kubernetes.io/docs/concepts/overview/"
    )

    query, limit = search_provider.queries[0]
    assert query == '"Kubernetes" official documentation getting started'
    assert limit == 5
    assert "PRIVATE RESUME EVIDENCE" not in query
    assert "PRIVATE GAP REASON" not in query


def test_acquisition_failure_keeps_existing_local_planning_behavior() -> None:
    local_result = RetrievalResult(
        rank=1,
        score=0.8,
        chunk_id="local-chunk",
        document_title="Local Guide",
        section="Practice",
        content="Use the existing local guidance.",
    )

    def fail_acquisition(_gap: Gap) -> AcquisitionResult:
        raise RuntimeError("web unavailable")

    with patch(
        "backend.rag.planning_context.retrieve_chunks",
        return_value=[local_result],
    ):
        context = retrieve_planning_context(
            [_gap()],
            acquire_gap=fail_acquisition,
        )

    assert [chunk.chunk_id for chunk in context] == ["local-chunk"]


def test_plan_wide_acquisition_limit_is_two() -> None:
    attempted_areas: list[str] = []

    def acquire(gap: Gap) -> AcquisitionResult:
        attempted_areas.append(gap.area)
        return AcquisitionResult(
            status=AcquisitionStatus.NO_SEARCH_RESULTS,
            query=f'"{gap.area}" official documentation getting started',
            search_result_count=0,
        )

    with patch("backend.rag.planning_context.retrieve_chunks", return_value=[]):
        retrieve_planning_context(
            [_gap("Docker"), _gap("Kubernetes"), _gap("Python")],
            acquire_gap=acquire,
        )

    assert attempted_areas == ["Docker", "Kubernetes"]


def test_rag_flow_logs_safe_operational_details(caplog) -> None:
    gap = _gap()
    acquisition = AcquisitionResult(
        status=AcquisitionStatus.INGESTED,
        query='"Kubernetes" official documentation getting started',
        search_result_count=1,
        selected_url="https://kubernetes.io/docs/home/",
        ingestion_result=IngestionResult(
            document_id="kubernetes-doc",
            status=IngestionStatus.INSERTED,
            chunk_count=1,
        ),
    )
    result = RetrievalResult(
        rank=1,
        score=0.8,
        chunk_id="kubernetes-chunk",
        document_title="Kubernetes Documentation",
        section="Overview",
        content="Kubernetes learning guidance.",
    )

    caplog.set_level(logging.INFO, logger="uvicorn.error")
    with patch(
        "backend.rag.planning_context.retrieve_chunks",
        return_value=[result],
    ):
        retrieve_planning_context([gap], acquire_gap=lambda _gap: acquisition)

    messages = "\n".join(record.getMessage() for record in caplog.records)
    assert "[RAG] Gap: Kubernetes" in messages
    assert "[RAG] Web acquisition: attempted" in messages
    assert "[RAG] Acquisition attempt: 1/2" in messages
    assert (
        '[RAG] Search query: "Kubernetes" official documentation getting started'
        in messages
    )
    assert "[RAG] Selected source: https://kubernetes.io/docs/home/" in messages
    assert "[RAG] Acquisition status: ingested" in messages
    assert "[RAG] Ingestion status: inserted" in messages
    assert "[RAG] Retrieval results: 1" in messages
    assert "[RAG] Planning context chunks: 1" in messages
    assert "PRIVATE RESUME EVIDENCE" not in messages
    assert "PRIVATE GAP REASON" not in messages


def test_planning_retries_do_not_repeat_acquisition() -> None:
    gaps = [_gap("Docker")]
    invalid_plan = CareerActionPlan(
        actions=[
            PlannedAction(
                title="Learn Docker",
                description="Containerize a service.",
                addresses_gaps=["Unknown gap"],
                priority=1,
                depends_on=[],
            )
        ]
    )
    valid_plan = CareerActionPlan(
        actions=[
            PlannedAction(
                title="Learn Docker",
                description="Containerize a service.",
                addresses_gaps=["Docker"],
                priority=1,
                depends_on=[],
            )
        ]
    )

    with (
        patch(
            "backend.rag.planning_context.acquire_gap_source_from_web",
            return_value=AcquisitionResult(
                status=AcquisitionStatus.NO_SEARCH_RESULTS,
                query='"Docker" official documentation getting started',
                search_result_count=0,
            ),
        ) as mock_acquire,
        patch("backend.rag.planning_context.retrieve_chunks", return_value=[]),
        patch(
            "backend.services.planner_service.generate_career_action_plan",
            side_effect=[invalid_plan, valid_plan],
        ),
    ):
        result = create_validated_career_action_plan(gaps)

    assert result == valid_plan
    mock_acquire.assert_called_once()
