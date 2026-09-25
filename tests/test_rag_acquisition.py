from datetime import datetime, timezone
from pathlib import Path

from backend.models.analysis import Gap, MatchStatus
from backend.rag.acquisition import acquire_and_ingest_gap_source
from backend.rag.models import IngestionResult, IngestionStatus
from backend.rag.web_models import (
    AcquisitionStatus,
    FetchedWebPage,
    SelectedWebSource,
    WebSearchResult,
)
from backend.rag.web_sources import WebFetchError


NOW = datetime(2026, 9, 23, 16, 0, tzinfo=timezone.utc)
HTML = b"""
<html><body><main>
<h1>Docker getting started</h1>
<p>Docker packages an application and its dependencies into a container image.</p>
<p>Build the image, run a local container, inspect logs, and document the workflow.</p>
</main></body></html>
"""


def _gap(area: str = "Docker") -> Gap:
    return Gap(
        area=area,
        status=MatchStatus.PARTIAL,
        evidence="PRIVATE_RESUME_EVIDENCE",
        reason="PRIVATE_MATCH_REASON",
    )


class FakeSearchProvider:
    def __init__(self, results: list[WebSearchResult]) -> None:
        self.results = results
        self.calls: list[tuple[str, int]] = []

    def search(self, query: str, *, limit: int) -> list[WebSearchResult]:
        self.calls.append((query, limit))
        return self.results


class FakeFetcher:
    def __init__(self, *, fail_first: bool = False) -> None:
        self.fail_first = fail_first
        self.calls: list[SelectedWebSource] = []

    def fetch(self, source: SelectedWebSource) -> FetchedWebPage:
        self.calls.append(source)
        if self.fail_first and len(self.calls) == 1:
            raise WebFetchError("first candidate failed")
        return FetchedWebPage(
            requested_url=source.canonical_url,
            final_url=source.canonical_url,
            content_type="text/html",
            encoding="utf-8",
            body=HTML,
            fetched_at=NOW,
        )


def _result(url: str, rank: int) -> WebSearchResult:
    return WebSearchResult(
        title="Docker official documentation",
        url=url,
        snippet="Docker getting started documentation.",
        rank=rank,
        provider="test",
    )


def test_acquisition_normalizes_and_delegates_to_checkpoint_one(tmp_path: Path) -> None:
    provider = FakeSearchProvider(
        [_result("https://docs.docker.com/get-started/", 1)]
    )
    fetcher = FakeFetcher()
    ingested_sources = []

    def fake_ingest(source, **kwargs):
        ingested_sources.append((source, kwargs))
        return IngestionResult(
            document_id="web-document",
            status=IngestionStatus.INSERTED,
            chunk_count=2,
        )

    result = acquire_and_ingest_gap_source(
        _gap(),
        search_provider=provider,
        page_fetcher=fetcher,
        database_path=tmp_path / "knowledge.db",
        ingest_function=fake_ingest,
    )

    assert result.status == AcquisitionStatus.INGESTED
    assert result.ingestion_result is not None
    assert result.ingestion_result.status == IngestionStatus.INSERTED
    assert len(ingested_sources) == 1
    assert ingested_sources[0][0] == result.source
    assert provider.calls[0][1] == 5
    assert "Docker" in provider.calls[0][0]
    assert "PRIVATE_RESUME_EVIDENCE" not in provider.calls[0][0]
    assert "PRIVATE_MATCH_REASON" not in provider.calls[0][0]


def test_unknown_authority_stops_before_fetch_or_ingestion(tmp_path: Path) -> None:
    provider = FakeSearchProvider(
        [
            WebSearchResult(
                title="React documentation",
                url="https://react.dev/learn",
                snippet="Learn React.",
                rank=1,
                provider="test",
            )
        ]
    )
    fetcher = FakeFetcher()
    ingest_calls = []

    result = acquire_and_ingest_gap_source(
        _gap("React"),
        search_provider=provider,
        page_fetcher=fetcher,
        database_path=tmp_path / "knowledge.db",
        ingest_function=lambda *args, **kwargs: ingest_calls.append(args),
    )

    assert result.status == AcquisitionStatus.NO_TRUSTED_SOURCE
    assert fetcher.calls == []
    assert ingest_calls == []


def test_acquisition_tries_at_most_two_trusted_candidates(tmp_path: Path) -> None:
    provider = FakeSearchProvider(
        [
            _result("https://docs.docker.com/first", 1),
            _result("https://docs.docker.com/second", 2),
            _result("https://docs.docker.com/third", 3),
        ]
    )
    fetcher = FakeFetcher(fail_first=True)
    ingest_count = 0

    def fake_ingest(source, **kwargs):
        nonlocal ingest_count
        ingest_count += 1
        return IngestionResult(
            document_id="web-document",
            status=IngestionStatus.INSERTED,
            chunk_count=1,
        )

    result = acquire_and_ingest_gap_source(
        _gap(),
        search_provider=provider,
        page_fetcher=fetcher,
        database_path=tmp_path / "knowledge.db",
        ingest_function=fake_ingest,
    )

    assert result.status == AcquisitionStatus.INGESTED
    assert len(fetcher.calls) == 2
    assert fetcher.calls[-1].canonical_url.endswith("/second")
    assert ingest_count == 1
