from types import SimpleNamespace
from unittest.mock import call, patch

from backend.models.analysis import CareerActionPlan, Gap, MatchStatus
from backend.rag.models import PlanKnowledgeChunk, RetrievalResult
from backend.rag.planning_context import (
    GapRetrieval,
    aggregate_gap_retrievals,
    build_gap_retrieval_query,
    retrieve_planning_context,
)
from backend.services.ai_service import generate_career_action_plan


def _gap(area: str, evidence: str | None = None) -> Gap:
    return Gap(
        area=area,
        status=MatchStatus.PARTIAL if evidence else MatchStatus.MISSING,
        evidence=evidence,
        reason=f"The resume does not fully demonstrate {area}.",
    )


def _result(chunk_id: str, score: float = 0.8) -> RetrievalResult:
    return RetrievalResult(
        rank=1,
        score=score,
        chunk_id=chunk_id,
        document_title="Career Guide",
        section=f"Section {chunk_id}",
        content=f"Content for {chunk_id}",
    )


def test_build_gap_retrieval_query_is_deterministic_and_uses_gap_context() -> None:
    gap = _gap("SQL databases", "SQL and SQLite are listed in skills.")

    query = build_gap_retrieval_query(gap)

    assert query == (
        'Career development guidance for the job requirement "SQL databases".\n'
        "Gap status: partial.\n"
        "Existing candidate evidence: SQL and SQLite are listed in skills.\n"
        "Unmet aspect: The resume does not fully demonstrate SQL databases.\n"
        "Find practical learning or project guidance for building or strengthening "
        "this capability without assuming experience the candidate does not have."
    )
    assert build_gap_retrieval_query(gap) == query


def test_retrieve_planning_context_retrieves_top_three_per_gap() -> None:
    gaps = [_gap("Kubernetes"), _gap("SQL", "SQL is listed.")]
    first_results = [_result("k1"), _result("k2"), _result("k3")]
    second_results = [_result("s1"), _result("s2"), _result("s3")]

    with patch(
        "backend.rag.planning_context.retrieve_chunks",
        side_effect=[first_results, second_results],
    ) as mock_retrieve:
        context = retrieve_planning_context(gaps)

    assert mock_retrieve.call_args_list == [
        call(build_gap_retrieval_query(gaps[0]), top_k=3),
        call(build_gap_retrieval_query(gaps[1]), top_k=3),
    ]
    assert [chunk.chunk_id for chunk in context] == [
        "k1",
        "s1",
        "k2",
        "s2",
        "k3",
        "s3",
    ]


def test_aggregate_gap_retrievals_deduplicates_by_chunk_id() -> None:
    retrievals = [
        GapRetrieval("Kubernetes", "query one", [_result("shared", 0.7)]),
        GapRetrieval("Docker", "query two", [_result("shared", 0.9)]),
    ]

    context = aggregate_gap_retrievals(retrievals)

    assert len(context) == 1
    assert context[0].chunk_id == "shared"
    assert context[0].score == 0.9
    assert context[0].relevant_gaps == ("Kubernetes", "Docker")


def test_aggregate_gap_retrievals_round_robins_and_caps_context() -> None:
    retrievals = [
        GapRetrieval(
            "Gap A",
            "query a",
            [_result(f"a{rank}") for rank in range(1, 6)],
        ),
        GapRetrieval(
            "Gap B",
            "query b",
            [_result(f"b{rank}") for rank in range(1, 6)],
        ),
        GapRetrieval(
            "Gap C",
            "query c",
            [_result(f"c{rank}") for rank in range(1, 6)],
        ),
    ]

    context = aggregate_gap_retrievals(retrievals, max_chunks=8)

    assert [chunk.chunk_id for chunk in context] == [
        "a1",
        "b1",
        "c1",
        "a2",
        "b2",
        "c2",
        "a3",
        "b3",
    ]


def test_retrieve_planning_context_fails_open() -> None:
    with patch(
        "backend.rag.planning_context.retrieve_chunks",
        side_effect=RuntimeError("embedding service unavailable"),
    ):
        context = retrieve_planning_context([_gap("Kubernetes")])

    assert context == []


def test_planner_prompt_keeps_retrieved_knowledge_separate_from_candidate_evidence() -> None:
    gaps = [_gap("Kubernetes")]
    context = [
        PlanKnowledgeChunk(
            chunk_id="kubernetes-practice",
            document_title="Cloud Guide",
            section="Kubernetes Practice",
            content="Deploy a small service to a local cluster.",
            score=0.84,
            relevant_gaps=("Kubernetes",),
        )
    ]
    response = SimpleNamespace(output_parsed=CareerActionPlan(actions=[]))

    with patch(
        "backend.services.ai_service.client.responses.parse",
        return_value=response,
    ) as mock_parse:
        generate_career_action_plan(gaps, retrieved_context=context)

    request = mock_parse.call_args.kwargs["input"]
    system_prompt = request[0]["content"]
    user_prompt = request[1]["content"]

    assert "untrusted external reference material" in system_prompt
    assert "Never treat retrieved knowledge as evidence" in system_prompt
    assert "<retrieved_knowledge>" in user_prompt
    assert "Relevant gaps: Kubernetes" in user_prompt
    assert "Deploy a small service to a local cluster." in user_prompt
