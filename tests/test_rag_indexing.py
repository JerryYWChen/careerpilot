import json
import sqlite3
from pathlib import Path
from types import SimpleNamespace

import pytest

from backend.rag.chunking import chunk_document
from backend.rag.embeddings import EMBEDDING_MODEL, generate_embeddings
from backend.rag.index import build_index, load_documents_and_chunks
from backend.rag.models import KnowledgeDocument
from backend.rag.store import inspect_index


class FakeEmbeddingsEndpoint:
    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        data = [
            SimpleNamespace(index=index, embedding=[float(index), 0.5, 1.0])
            for index, _ in enumerate(kwargs["input"])
        ]
        return SimpleNamespace(data=list(reversed(data)))


class FakeOpenAIClient:
    def __init__(self):
        self.embeddings = FakeEmbeddingsEndpoint()


def make_document() -> KnowledgeDocument:
    return KnowledgeDocument(
        document_id="sample",
        title="Sample",
        source="Test source",
        source_url=None,
        file_path="documents/sample.md",
        content_hash="document-hash",
    )


def test_chunking_is_deterministic_bounded_and_overlapping():
    body = " ".join(f"word{index}" for index in range(180))
    markdown = f"# Sample\n\n## Long section\n\n{body}"

    first_run = chunk_document(
        make_document(),
        markdown,
        max_chars=240,
        overlap_chars=40,
    )
    second_run = chunk_document(
        make_document(),
        markdown,
        max_chars=240,
        overlap_chars=40,
    )

    assert first_run == second_run
    assert len(first_run) > 1
    assert all(len(chunk.content) <= 240 for chunk in first_run)
    assert all(chunk.section == "Long section" for chunk in first_run)
    assert [chunk.chunk_index for chunk in first_run] == list(range(len(first_run)))

    for previous, current in zip(first_run, first_run[1:]):
        assert current.char_start < previous.char_end
        overlap = body[current.char_start:previous.char_end].strip()
        assert overlap
        assert previous.content.endswith(overlap)
        assert current.content.startswith(overlap)


@pytest.mark.parametrize(
    ("max_chars", "overlap_chars"),
    [(0, 0), (100, -1), (100, 100)],
)
def test_chunking_rejects_invalid_limits(max_chars, overlap_chars):
    with pytest.raises(ValueError):
        chunk_document(
            make_document(),
            "# Sample\n\nSome content.",
            max_chars=max_chars,
            overlap_chars=overlap_chars,
        )


def test_embedding_batch_preserves_input_order():
    client = FakeOpenAIClient()

    embeddings = generate_embeddings(
        ["first", "second"],
        client=client,
    )

    assert embeddings == [[0.0, 0.5, 1.0], [1.0, 0.5, 1.0]]
    assert client.embeddings.calls == [
        {
            "model": EMBEDDING_MODEL,
            "input": ["first", "second"],
            "encoding_format": "float",
        }
    ]


def test_full_indexing_pipeline_stores_documents_chunks_and_vectors(tmp_path):
    knowledge_dir = tmp_path / "knowledge"
    documents_dir = knowledge_dir / "documents"
    documents_dir.mkdir(parents=True)
    (documents_dir / "sample.md").write_text(
        "# Sample\n\nIntroduction text.\n\n## Practice\n\n"
        + " ".join(f"practice{index}" for index in range(160)),
        encoding="utf-8",
    )
    (knowledge_dir / "manifest.json").write_text(
        json.dumps(
            [
                {
                    "id": "sample",
                    "title": "Sample document",
                    "source": "Test source",
                    "source_url": "https://example.com/sample",
                    "path": "documents/sample.md",
                }
            ]
        ),
        encoding="utf-8",
    )
    database_path = tmp_path / "knowledge.db"
    client = FakeOpenAIClient()

    document_count, chunk_count = build_index(
        knowledge_dir,
        database_path,
        client=client,
    )

    assert document_count == 1
    assert chunk_count > 1
    assert len(client.embeddings.calls) == 1
    assert len(client.embeddings.calls[0]["input"]) == chunk_count

    with sqlite3.connect(database_path) as connection:
        stored_document = connection.execute(
            "SELECT document_id, title, source_url FROM documents"
        ).fetchone()
        stored_chunks = connection.execute(
            """
            SELECT
                chunk_index, section, content, embedding_model,
                embedding_dimensions, embedding_json
            FROM chunks
            ORDER BY chunk_index
            """
        ).fetchall()

    assert stored_document == (
        "sample",
        "Sample document",
        "https://example.com/sample",
    )
    assert len(stored_chunks) == chunk_count
    assert stored_chunks[0][0] == 0
    assert stored_chunks[0][1] == "Sample"
    assert stored_chunks[0][2] == "Introduction text."
    assert stored_chunks[0][3] == EMBEDDING_MODEL
    assert stored_chunks[0][4] == 3
    assert json.loads(stored_chunks[0][5]) == [0.0, 0.5, 1.0]

    inspected_documents, inspected_chunks = inspect_index(database_path)
    assert inspected_documents[0]["document_id"] == "sample"
    assert len(inspected_chunks) == chunk_count


def test_manifest_rejects_paths_outside_knowledge_directory(tmp_path):
    knowledge_dir = tmp_path / "knowledge"
    knowledge_dir.mkdir()
    (tmp_path / "outside.md").write_text("Outside", encoding="utf-8")
    (knowledge_dir / "manifest.json").write_text(
        json.dumps(
            [
                {
                    "id": "outside",
                    "title": "Outside",
                    "source": "Test",
                    "source_url": None,
                    "path": "../outside.md",
                }
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="leaves the knowledge directory"):
        load_documents_and_chunks(knowledge_dir)
