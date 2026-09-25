import hashlib
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from backend.rag.embeddings import EMBEDDING_MODEL
from backend.rag.ingest import ingest_knowledge_source
from backend.rag.models import (
    IngestionStatus,
    KnowledgeChunk,
    KnowledgeDocument,
    NormalizedKnowledgeSource,
)
from backend.rag.store import inspect_index, write_index


class FakeEmbeddingsEndpoint:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            data=[
                SimpleNamespace(index=index, embedding=[float(index), 1.0])
                for index, _ in enumerate(kwargs["input"])
            ]
        )


class FakeOpenAIClient:
    def __init__(self) -> None:
        self.embeddings = FakeEmbeddingsEndpoint()


def _hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _source(content: str, *, title: str = "Official Docker Guide"):
    retrieved_at = datetime(2026, 9, 23, 16, 0, tzinfo=timezone.utc)
    return NormalizedKnowledgeSource(
        title=title,
        canonical_url="https://docs.example.com/docker/guide",
        source_type="official_documentation",
        retrieved_at=retrieved_at,
        last_checked_at=retrieved_at,
        content=content,
        content_hash=_hash(content),
    )


def _write_manual_document(database_path: Path) -> None:
    document = KnowledgeDocument(
        document_id="manual-guide",
        title="Manual Career Guide",
        source="CareerPilot sample knowledge base",
        source_url=None,
        file_path="documents/manual.md",
        content_hash="manual-document-hash",
    )
    chunk = KnowledgeChunk(
        chunk_id="manual-chunk",
        document_id=document.document_id,
        document_title=document.title,
        source=document.source,
        source_url=document.source_url,
        file_path=document.file_path,
        section="Manual",
        chunk_index=0,
        char_start=0,
        char_end=20,
        content="Existing manual text.",
        content_hash="manual-chunk-hash",
    )
    write_index(
        database_path,
        [document],
        [chunk],
        [[1.0, 0.0]],
        EMBEDDING_MODEL,
    )


def test_incremental_ingestion_inserts_source_and_preserves_manual_knowledge(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "knowledge.db"
    _write_manual_document(database_path)
    client = FakeOpenAIClient()

    result = ingest_knowledge_source(
        _source("# Docker\n\nBuild and run a container image."),
        database_path=database_path,
        client=client,
    )

    assert result.status == IngestionStatus.INSERTED
    assert result.chunk_count == 1
    assert len(client.embeddings.calls) == 1

    documents, chunks = inspect_index(database_path)
    assert {row["document_id"] for row in documents} == {
        "manual-guide",
        result.document_id,
    }
    assert {row["document_id"] for row in chunks} == {
        "manual-guide",
        result.document_id,
    }


def test_incremental_ingestion_persists_source_metadata(tmp_path: Path) -> None:
    database_path = tmp_path / "knowledge.db"
    source = _source("# Docker\n\nBuild and run a container image.")

    result = ingest_knowledge_source(
        source,
        database_path=database_path,
        client=FakeOpenAIClient(),
    )

    with sqlite3.connect(database_path) as connection:
        row = connection.execute(
            """
            SELECT title, source_url, source_type, retrieved_at,
                   last_checked_at, content_hash
            FROM documents
            WHERE document_id = ?
            """,
            (result.document_id,),
        ).fetchone()

    assert row == (
        source.title,
        source.canonical_url,
        source.source_type,
        source.retrieved_at.isoformat(),
        source.last_checked_at.isoformat(),
        source.content_hash,
    )


def test_reingesting_unchanged_source_skips_embedding(tmp_path: Path) -> None:
    database_path = tmp_path / "knowledge.db"
    source = _source("# Docker\n\nBuild and run a container image.")
    client = FakeOpenAIClient()

    first = ingest_knowledge_source(
        source,
        database_path=database_path,
        client=client,
    )
    second = ingest_knowledge_source(
        source,
        database_path=database_path,
        client=client,
    )

    assert first.status == IngestionStatus.INSERTED
    assert second == type(second)(
        document_id=first.document_id,
        status=IngestionStatus.UNCHANGED,
        chunk_count=first.chunk_count,
    )
    assert len(client.embeddings.calls) == 1


def test_changed_source_replaces_only_its_own_chunks(tmp_path: Path) -> None:
    database_path = tmp_path / "knowledge.db"
    _write_manual_document(database_path)
    client = FakeOpenAIClient()

    original = ingest_knowledge_source(
        _source("# Docker\n\nOld guidance."),
        database_path=database_path,
        client=client,
    )
    changed_source = _source(
        "# Docker\n\nUpdated guidance.\n\n## Practice\n\nBuild a small image.",
        title="Updated Official Docker Guide",
    )
    replaced = ingest_knowledge_source(
        changed_source,
        database_path=database_path,
        client=client,
    )

    assert replaced.document_id == original.document_id
    assert replaced.status == IngestionStatus.REPLACED
    assert len(client.embeddings.calls) == 2

    documents, chunks = inspect_index(database_path)
    stored_documents = {row["document_id"]: row for row in documents}
    assert set(stored_documents) == {"manual-guide", original.document_id}
    assert stored_documents[original.document_id]["title"] == changed_source.title
    assert (
        stored_documents[original.document_id]["content_hash"]
        == changed_source.content_hash
    )
    assert any(row["chunk_id"] == "manual-chunk" for row in chunks)
    web_chunks = [
        row for row in chunks if row["document_id"] == original.document_id
    ]
    assert len(web_chunks) == 2
    assert all("Old guidance." not in row["content"] for row in web_chunks)
