from dataclasses import dataclass


@dataclass(frozen=True)
class KnowledgeDocument:
    document_id: str
    title: str
    source: str
    source_url: str | None
    file_path: str
    content_hash: str


@dataclass(frozen=True)
class KnowledgeChunk:
    chunk_id: str
    document_id: str
    document_title: str
    source: str
    source_url: str | None
    file_path: str
    section: str
    chunk_index: int
    char_start: int
    char_end: int
    content: str
    content_hash: str


@dataclass(frozen=True)
class EmbeddedChunk:
    chunk_id: str
    document_title: str
    section: str
    content: str
    embedding_model: str
    embedding_dimensions: int
    embedding: list[float]


@dataclass(frozen=True)
class RetrievalResult:
    rank: int
    score: float
    chunk_id: str
    document_title: str
    section: str
    content: str


@dataclass(frozen=True)
class PlanKnowledgeChunk:
    chunk_id: str
    document_title: str
    section: str
    content: str
    score: float
    relevant_gaps: tuple[str, ...]
