from collections.abc import Callable
from pathlib import Path

from backend.models.analysis import Gap
from backend.rag.ingest import ingest_knowledge_source
from backend.rag.models import IngestionResult, NormalizedKnowledgeSource
from backend.rag.retrieve import DEFAULT_DATABASE_PATH
from backend.rag.web_models import AcquisitionResult, AcquisitionStatus
from backend.rag.web_search import (
    BraveWebSearchProvider,
    MAX_SEARCH_RESULTS,
    WebSearchError,
    WebSearchProvider,
    build_web_search_query,
)
from backend.rag.web_sources import (
    HttpxWebPageFetcher,
    SourceExtractionError,
    WebFetchError,
    WebPageFetcher,
    normalize_web_page,
    select_trusted_sources,
)


IngestFunction = Callable[..., IngestionResult]


def acquire_gap_source_from_web(
    gap: Gap,
    *,
    database_path: Path = DEFAULT_DATABASE_PATH,
    embedding_client=None,
) -> AcquisitionResult:
    """Run the configured Brave acquisition path for one gap."""
    try:
        search_provider = BraveWebSearchProvider()
    except ValueError as error:
        return AcquisitionResult(
            status=AcquisitionStatus.SEARCH_FAILED,
            query=build_web_search_query(gap),
            search_result_count=0,
            error=str(error),
        )

    page_fetcher = HttpxWebPageFetcher()
    try:
        return acquire_and_ingest_gap_source(
            gap,
            search_provider=search_provider,
            page_fetcher=page_fetcher,
            database_path=database_path,
            embedding_client=embedding_client,
        )
    finally:
        search_provider.client.close()
        page_fetcher.client.close()


def acquire_and_ingest_gap_source(
    gap: Gap,
    *,
    search_provider: WebSearchProvider,
    page_fetcher: WebPageFetcher,
    database_path: Path = DEFAULT_DATABASE_PATH,
    embedding_client=None,
    ingest_function: IngestFunction | None = None,
) -> AcquisitionResult:
    query = build_web_search_query(gap)

    try:
        search_results = search_provider.search(query, limit=MAX_SEARCH_RESULTS)
    except WebSearchError as error:
        return AcquisitionResult(
            status=AcquisitionStatus.SEARCH_FAILED,
            query=query,
            search_result_count=0,
            error=str(error),
        )

    search_results = search_results[:MAX_SEARCH_RESULTS]
    if not search_results:
        return AcquisitionResult(
            status=AcquisitionStatus.NO_SEARCH_RESULTS,
            query=query,
            search_result_count=0,
        )

    selected_sources = select_trusted_sources(gap, search_results)
    if not selected_sources:
        return AcquisitionResult(
            status=AcquisitionStatus.NO_TRUSTED_SOURCE,
            query=query,
            search_result_count=len(search_results),
        )

    last_status = AcquisitionStatus.FETCH_FAILED
    last_error: str | None = None

    for selected_source in selected_sources:
        try:
            page = page_fetcher.fetch(selected_source)
        except WebFetchError as error:
            last_status = AcquisitionStatus.FETCH_FAILED
            last_error = str(error)
            continue

        try:
            normalized_source = normalize_web_page(selected_source, page)
        except SourceExtractionError as error:
            last_status = AcquisitionStatus.EXTRACTION_FAILED
            last_error = str(error)
            continue

        ingest = ingest_function or ingest_knowledge_source
        try:
            ingestion_result = ingest(
                normalized_source,
                database_path=database_path,
                client=embedding_client,
            )
        except Exception as error:
            return AcquisitionResult(
                status=AcquisitionStatus.INGESTION_FAILED,
                query=query,
                search_result_count=len(search_results),
                selected_url=normalized_source.canonical_url,
                source=normalized_source,
                error=str(error),
            )

        return AcquisitionResult(
            status=AcquisitionStatus.INGESTED,
            query=query,
            search_result_count=len(search_results),
            selected_url=normalized_source.canonical_url,
            source=normalized_source,
            ingestion_result=ingestion_result,
        )

    return AcquisitionResult(
        status=last_status,
        query=query,
        search_result_count=len(search_results),
        selected_url=selected_sources[-1].canonical_url,
        error=last_error,
    )
