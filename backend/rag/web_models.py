from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from backend.rag.models import IngestionResult, NormalizedKnowledgeSource


@dataclass(frozen=True)
class WebSearchResult:
    title: str
    url: str
    snippet: str | None
    rank: int
    provider: str


@dataclass(frozen=True)
class AuthorityRule:
    aliases: tuple[str, ...]
    allowed_host: str
    source_type: str
    path_prefixes: tuple[str, ...] = ()
    path_fragments: tuple[str, ...] = ()


@dataclass(frozen=True)
class SelectedWebSource:
    result: WebSearchResult
    canonical_url: str
    rule: AuthorityRule


@dataclass(frozen=True)
class FetchedWebPage:
    requested_url: str
    final_url: str
    content_type: str
    encoding: str
    body: bytes
    fetched_at: datetime


class AcquisitionStatus(str, Enum):
    INGESTED = "ingested"
    NO_SEARCH_RESULTS = "no_search_results"
    NO_TRUSTED_SOURCE = "no_trusted_source"
    SEARCH_FAILED = "search_failed"
    FETCH_FAILED = "fetch_failed"
    EXTRACTION_FAILED = "extraction_failed"
    INGESTION_FAILED = "ingestion_failed"


@dataclass(frozen=True)
class AcquisitionResult:
    status: AcquisitionStatus
    query: str
    search_result_count: int
    selected_url: str | None = None
    source: NormalizedKnowledgeSource | None = None
    ingestion_result: IngestionResult | None = None
    error: str | None = None
