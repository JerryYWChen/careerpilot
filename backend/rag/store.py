import json
import sqlite3
from pathlib import Path

from backend.rag.models import EmbeddedChunk, KnowledgeChunk, KnowledgeDocument


SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    document_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    source TEXT NOT NULL,
    source_url TEXT,
    file_path TEXT NOT NULL,
    content_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chunks (
    chunk_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    document_title TEXT NOT NULL,
    source TEXT NOT NULL,
    source_url TEXT,
    file_path TEXT NOT NULL,
    section TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    char_start INTEGER NOT NULL,
    char_end INTEGER NOT NULL,
    content TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    embedding_model TEXT NOT NULL,
    embedding_dimensions INTEGER NOT NULL,
    embedding_json TEXT NOT NULL,
    FOREIGN KEY (document_id) REFERENCES documents(document_id)
);

CREATE INDEX IF NOT EXISTS idx_chunks_document_id
ON chunks(document_id);
"""


def write_index(
    database_path: Path,
    documents: list[KnowledgeDocument],
    chunks: list[KnowledgeChunk],
    embeddings: list[list[float]],
    embedding_model: str,
) -> None:
    if len(chunks) != len(embeddings):
        raise ValueError("Every chunk must have exactly one embedding.")

    database_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(SCHEMA)

        with connection:
            connection.execute("DELETE FROM chunks")
            connection.execute("DELETE FROM documents")

            connection.executemany(
                """
                INSERT INTO documents (
                    document_id, title, source, source_url,
                    file_path, content_hash
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        document.document_id,
                        document.title,
                        document.source,
                        document.source_url,
                        document.file_path,
                        document.content_hash,
                    )
                    for document in documents
                ],
            )

            connection.executemany(
                """
                INSERT INTO chunks (
                    chunk_id, document_id, document_title, source,
                    source_url, file_path, section, chunk_index,
                    char_start, char_end, content, content_hash,
                    embedding_model, embedding_dimensions, embedding_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        chunk.chunk_id,
                        chunk.document_id,
                        chunk.document_title,
                        chunk.source,
                        chunk.source_url,
                        chunk.file_path,
                        chunk.section,
                        chunk.chunk_index,
                        chunk.char_start,
                        chunk.char_end,
                        chunk.content,
                        chunk.content_hash,
                        embedding_model,
                        len(embedding),
                        json.dumps(embedding, separators=(",", ":")),
                    )
                    for chunk, embedding in zip(chunks, embeddings, strict=True)
                ],
            )


def inspect_index(
    database_path: Path,
) -> tuple[list[sqlite3.Row], list[sqlite3.Row]]:
    if not database_path.exists():
        raise FileNotFoundError(f"Knowledge index not found: {database_path}")

    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        documents = connection.execute(
            """
            SELECT
                document_id,
                title,
                source,
                source_url,
                file_path,
                content_hash
            FROM documents
            ORDER BY document_id
            """
        ).fetchall()
        chunks = connection.execute(
            """
            SELECT
                chunk_id,
                document_id,
                document_title,
                section,
                chunk_index,
                char_start,
                char_end,
                content,
                content_hash,
                embedding_model,
                embedding_dimensions
            FROM chunks
            ORDER BY document_id, chunk_index
            """
        ).fetchall()
        return documents, chunks


def load_embedded_chunks(database_path: Path) -> list[EmbeddedChunk]:
    if not database_path.exists():
        raise FileNotFoundError(f"Knowledge index not found: {database_path}")

    with sqlite3.connect(database_path) as connection:
        rows = connection.execute(
            """
            SELECT
                chunk_id,
                document_title,
                section,
                content,
                embedding_model,
                embedding_dimensions,
                embedding_json
            FROM chunks
            ORDER BY chunk_id
            """
        ).fetchall()

    return [
        EmbeddedChunk(
            chunk_id=row[0],
            document_title=row[1],
            section=row[2],
            content=row[3],
            embedding_model=row[4],
            embedding_dimensions=row[5],
            embedding=json.loads(row[6]),
        )
        for row in rows
    ]
