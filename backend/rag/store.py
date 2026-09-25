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
    content_hash TEXT NOT NULL,
    source_type TEXT NOT NULL DEFAULT 'manual',
    retrieved_at TEXT,
    last_checked_at TEXT
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

CREATE INDEX IF NOT EXISTS idx_documents_source_url
ON documents(source_url);
"""


def _ensure_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(SCHEMA)
    document_columns = {
        row[1]
        for row in connection.execute("PRAGMA table_info(documents)").fetchall()
    }

    migrations = {
        "source_type": "TEXT NOT NULL DEFAULT 'manual'",
        "retrieved_at": "TEXT",
        "last_checked_at": "TEXT",
    }
    for column_name, definition in migrations.items():
        if column_name not in document_columns:
            connection.execute(
                f"ALTER TABLE documents ADD COLUMN {column_name} {definition}"
            )


def _timestamp(value) -> str | None:
    return value.isoformat() if value is not None else None


def _document_row(document: KnowledgeDocument) -> tuple:
    return (
        document.document_id,
        document.title,
        document.source,
        document.source_url,
        document.file_path,
        document.content_hash,
        document.source_type,
        _timestamp(document.retrieved_at),
        _timestamp(document.last_checked_at),
    )


def _chunk_rows(
    chunks: list[KnowledgeChunk],
    embeddings: list[list[float]],
    embedding_model: str,
) -> list[tuple]:
    return [
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
    ]


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
        _ensure_schema(connection)

        with connection:
            connection.execute("DELETE FROM chunks")
            connection.execute("DELETE FROM documents")

            connection.executemany(
                """
                INSERT INTO documents (
                    document_id, title, source, source_url,
                    file_path, content_hash, source_type,
                    retrieved_at, last_checked_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [_document_row(document) for document in documents],
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
                _chunk_rows(chunks, embeddings, embedding_model),
            )


def get_document_by_source_url(
    database_path: Path,
    source_url: str,
) -> sqlite3.Row | None:
    if not database_path.exists():
        return None

    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        _ensure_schema(connection)
        return connection.execute(
            """
            SELECT
                document_id,
                title,
                source,
                source_url,
                file_path,
                content_hash,
                source_type,
                retrieved_at,
                last_checked_at,
                (
                    SELECT COUNT(*)
                    FROM chunks
                    WHERE chunks.document_id = documents.document_id
                ) AS chunk_count
            FROM documents
            WHERE source_url = ?
            ORDER BY document_id
            LIMIT 1
            """,
            (source_url,),
        ).fetchone()


def upsert_document(
    database_path: Path,
    document: KnowledgeDocument,
    chunks: list[KnowledgeChunk],
    embeddings: list[list[float]],
    embedding_model: str,
) -> None:
    if len(chunks) != len(embeddings):
        raise ValueError("Every chunk must have exactly one embedding.")
    if any(chunk.document_id != document.document_id for chunk in chunks):
        raise ValueError("Every chunk must belong to the document being upserted.")

    database_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        _ensure_schema(connection)

        with connection:
            conflicting_ids = [
                row[0]
                for row in connection.execute(
                    """
                    SELECT document_id
                    FROM documents
                    WHERE document_id = ? OR source_url = ?
                    """,
                    (document.document_id, document.source_url),
                ).fetchall()
            ]

            if conflicting_ids:
                placeholders = ", ".join("?" for _ in conflicting_ids)
                connection.execute(
                    f"DELETE FROM chunks WHERE document_id IN ({placeholders})",
                    conflicting_ids,
                )
                connection.execute(
                    f"DELETE FROM documents WHERE document_id IN ({placeholders})",
                    conflicting_ids,
                )

            connection.execute(
                """
                INSERT INTO documents (
                    document_id, title, source, source_url,
                    file_path, content_hash, source_type,
                    retrieved_at, last_checked_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                _document_row(document),
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
                _chunk_rows(chunks, embeddings, embedding_model),
            )


def inspect_index(
    database_path: Path,
) -> tuple[list[sqlite3.Row], list[sqlite3.Row]]:
    if not database_path.exists():
        raise FileNotFoundError(f"Knowledge index not found: {database_path}")

    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        _ensure_schema(connection)
        documents = connection.execute(
            """
            SELECT
                document_id,
                title,
                source,
                source_url,
                file_path,
                content_hash,
                source_type,
                retrieved_at,
                last_checked_at
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
        _ensure_schema(connection)
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
