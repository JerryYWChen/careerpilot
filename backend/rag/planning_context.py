from dataclasses import dataclass

from backend.models.analysis import Gap
from backend.rag.models import PlanKnowledgeChunk, RetrievalResult
from backend.rag.retrieve import retrieve_chunks


TOP_K_PER_GAP = 3
MAX_CONTEXT_CHUNKS = 8


@dataclass(frozen=True)
class GapRetrieval:
    gap_area: str
    query: str
    results: list[RetrievalResult]


def build_gap_retrieval_query(gap: Gap) -> str:
    evidence = (
        f"Existing candidate evidence: {gap.evidence.strip()}"
        if gap.evidence and gap.evidence.strip()
        else "No candidate evidence was identified for this requirement."
    )

    return (
        f'Career development guidance for the job requirement "{gap.area}".\n'
        f"Gap status: {gap.status.value}.\n"
        f"{evidence}\n"
        f"Unmet aspect: {gap.reason}\n"
        "Find practical learning or project guidance for building or strengthening "
        "this capability without assuming experience the candidate does not have."
    )


def aggregate_gap_retrievals(
    gap_retrievals: list[GapRetrieval],
    *,
    max_chunks: int = MAX_CONTEXT_CHUNKS,
) -> list[PlanKnowledgeChunk]:
    if max_chunks < 1:
        return []

    selected_order: list[str] = []
    selected: dict[str, PlanKnowledgeChunk] = {}
    result_depth = max(
        (len(gap_retrieval.results) for gap_retrieval in gap_retrievals),
        default=0,
    )

    for result_index in range(result_depth):
        for gap_retrieval in gap_retrievals:
            if result_index >= len(gap_retrieval.results):
                continue

            result = gap_retrieval.results[result_index]
            existing = selected.get(result.chunk_id)

            if existing is not None:
                relevant_gaps = existing.relevant_gaps
                if gap_retrieval.gap_area not in relevant_gaps:
                    relevant_gaps = (*relevant_gaps, gap_retrieval.gap_area)

                selected[result.chunk_id] = PlanKnowledgeChunk(
                    chunk_id=existing.chunk_id,
                    document_title=existing.document_title,
                    section=existing.section,
                    content=existing.content,
                    score=max(existing.score, result.score),
                    relevant_gaps=relevant_gaps,
                )
                continue

            if len(selected_order) >= max_chunks:
                continue

            selected_order.append(result.chunk_id)
            selected[result.chunk_id] = PlanKnowledgeChunk(
                chunk_id=result.chunk_id,
                document_title=result.document_title,
                section=result.section,
                content=result.content,
                score=result.score,
                relevant_gaps=(gap_retrieval.gap_area,),
            )

    return [selected[chunk_id] for chunk_id in selected_order]


def retrieve_planning_context(gaps: list[Gap]) -> list[PlanKnowledgeChunk]:
    gap_retrievals: list[GapRetrieval] = []

    try:
        for gap in gaps:
            query = build_gap_retrieval_query(gap)
            gap_retrievals.append(
                GapRetrieval(
                    gap_area=gap.area,
                    query=query,
                    results=retrieve_chunks(
                        query,
                        top_k=TOP_K_PER_GAP,
                    ),
                )
            )
    except Exception:
        return []

    return aggregate_gap_retrievals(gap_retrievals)
