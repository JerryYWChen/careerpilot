import logging
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from backend.models.analysis import Gap
from backend.rag.acquisition import acquire_gap_source_from_web
from backend.rag.models import PlanKnowledgeChunk, RetrievalResult
from backend.rag.retrieve import DEFAULT_DATABASE_PATH, retrieve_chunks
from backend.rag.web_models import AcquisitionResult


TOP_K_PER_GAP = 3
MAX_CONTEXT_CHUNKS = 8
MAX_ACQUISITION_ATTEMPTS_PER_PLAN = 2


GapAcquisitionFunction = Callable[[Gap], AcquisitionResult]
logger = logging.getLogger("uvicorn.error")


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


def retrieve_planning_context(
    gaps: list[Gap],
    *,
    database_path: Path = DEFAULT_DATABASE_PATH,
    embedding_client=None,
    acquire_gap: GapAcquisitionFunction | None = None,
) -> list[PlanKnowledgeChunk]:
    gap_retrievals: list[GapRetrieval] = []
    acquisition_attempts = 0

    if acquire_gap is None:
        acquire_gap = lambda gap: acquire_gap_source_from_web(
            gap,
            database_path=database_path,
            embedding_client=embedding_client,
        )

    try:
        for gap in gaps:
            logger.info("[RAG] Gap: %s", gap.area)

            if acquisition_attempts < MAX_ACQUISITION_ATTEMPTS_PER_PLAN:
                acquisition_attempts += 1
                logger.info("[RAG] Web acquisition: attempted")
                logger.info(
                    "[RAG] Acquisition attempt: %s/%s",
                    acquisition_attempts,
                    MAX_ACQUISITION_ATTEMPTS_PER_PLAN,
                )
                try:
                    acquisition_result = acquire_gap(gap)
                    logger.info(
                        "[RAG] Search query: %s",
                        acquisition_result.query,
                    )
                    if acquisition_result.selected_url:
                        logger.info(
                            "[RAG] Selected source: %s",
                            acquisition_result.selected_url,
                        )
                    logger.info(
                        "[RAG] Acquisition status: %s",
                        acquisition_result.status.value,
                    )
                    if acquisition_result.ingestion_result is not None:
                        logger.info(
                            "[RAG] Ingestion status: %s",
                            acquisition_result.ingestion_result.status.value,
                        )
                except Exception as error:
                    logger.warning(
                        "[RAG] Acquisition status: error (%s)",
                        type(error).__name__,
                    )
            else:
                logger.info(
                    "[RAG] Web acquisition: skipped (plan-wide limit reached)"
                )

            query = build_gap_retrieval_query(gap)
            retrieval_results = retrieve_chunks(
                query,
                database_path=database_path,
                top_k=TOP_K_PER_GAP,
                client=embedding_client,
            )
            logger.info("[RAG] Retrieval results: %s", len(retrieval_results))
            gap_retrievals.append(
                GapRetrieval(
                    gap_area=gap.area,
                    query=query,
                    results=retrieval_results,
                )
            )
    except Exception as error:
        logger.warning(
            "[RAG] Retrieval failed for gap %s (%s)",
            gap.area,
            type(error).__name__,
        )
        logger.info("[RAG] Retrieval results: 0")
        logger.info("[RAG] Planning context chunks: 0")
        return []

    planning_context = aggregate_gap_retrievals(gap_retrievals)
    logger.info("[RAG] Planning context chunks: %s", len(planning_context))
    return planning_context
