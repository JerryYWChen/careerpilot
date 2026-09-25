import hashlib
from pathlib import Path
from urllib.parse import urlsplit

from backend.rag.chunking import chunk_document
from backend.rag.embeddings import EMBEDDING_MODEL, generate_embeddings
from backend.rag.models import (
    IngestionResult,
    IngestionStatus,
    KnowledgeDocument,
    NormalizedKnowledgeSource,
)
from backend.rag.retrieve import DEFAULT_DATABASE_PATH
from backend.rag.store import get_document_by_source_url, upsert_document


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _document_id(canonical_url: str) -> str:
    return _hash_text(f"web:{canonical_url}")


def _validate_source(source: NormalizedKnowledgeSource) -> None:
    if not source.title.strip():
        raise ValueError("Knowledge source title must not be empty.")
    if not source.source_type.strip():
        raise ValueError("Knowledge source type must not be empty.")
    if not source.content.strip():
        raise ValueError("Knowledge source content must not be empty.")

    parsed_url = urlsplit(source.canonical_url)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        raise ValueError("Knowledge source canonical URL must be an HTTP(S) URL.")

    actual_hash = _hash_text(source.content)
    if source.content_hash != actual_hash:
        raise ValueError("Knowledge source content hash does not match its content.")


def ingest_knowledge_source(
    source: NormalizedKnowledgeSource,
    *,
    database_path: Path = DEFAULT_DATABASE_PATH,
    client=None,
) -> IngestionResult:
    _validate_source(source)

    existing = get_document_by_source_url(database_path, source.canonical_url)
    if existing is not None and existing["content_hash"] == source.content_hash:
        return IngestionResult(
            document_id=existing["document_id"],
            status=IngestionStatus.UNCHANGED,
            chunk_count=existing["chunk_count"],
        )

    document = KnowledgeDocument(
        document_id=_document_id(source.canonical_url),
        title=source.title.strip(),
        source=source.source_type.strip(),
        source_url=source.canonical_url,
        file_path=source.canonical_url,
        content_hash=source.content_hash,
        source_type=source.source_type.strip(),
        retrieved_at=source.retrieved_at,
        last_checked_at=source.last_checked_at,
    )
    chunks = chunk_document(document, source.content)
    if not chunks:
        raise ValueError("Knowledge source produced no chunks.")

    embeddings = generate_embeddings(
        [chunk.content for chunk in chunks],
        client=client,
        model=EMBEDDING_MODEL,
    )
    upsert_document(
        database_path,
        document,
        chunks,
        embeddings,
        EMBEDDING_MODEL,
    )

    return IngestionResult(
        document_id=document.document_id,
        status=(
            IngestionStatus.REPLACED
            if existing is not None
            else IngestionStatus.INSERTED
        ),
        chunk_count=len(chunks),
    )
