from pathlib import Path
from types import SimpleNamespace

import pytest

from backend.rag.embeddings import EMBEDDING_MODEL
from backend.rag.models import KnowledgeChunk, KnowledgeDocument, RetrievalResult
from backend.rag.retrieve import cosine_similarity, print_results, retrieve_chunks
from backend.rag.store import write_index


class FakeEmbeddingsEndpoint:
    def __init__(self, embedding: list[float]) -> None:
        self.embedding = embedding
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            data=[SimpleNamespace(index=0, embedding=self.embedding)]
        )


class FakeOpenAIClient:
    def __init__(self, embedding: list[float]) -> None:
        self.embeddings = FakeEmbeddingsEndpoint(embedding)


def _write_test_index(
    database_path: Path,
    *,
    embedding_model: str = EMBEDDING_MODEL,
) -> None:
    document = KnowledgeDocument(
        document_id="test-guide",
        title="Test Career Guide",
        source="test",
        source_url=None,
        file_path="test.md",
        content_hash="document-hash",
    )
    chunks = [
        KnowledgeChunk(
            chunk_id="python-api",
            document_id=document.document_id,
            document_title=document.title,
            source=document.source,
            source_url=None,
            file_path=document.file_path,
            section="Python APIs",
            chunk_index=0,
            char_start=0,
            char_end=17,
            content="Build Python APIs.",
            content_hash="python-hash",
        ),
        KnowledgeChunk(
            chunk_id="container-orchestration",
            document_id=document.document_id,
            document_title=document.title,
            source=document.source,
            source_url=None,
            file_path=document.file_path,
            section="Container Orchestration",
            chunk_index=1,
            char_start=18,
            char_end=42,
            content="Learn Kubernetes concepts.",
            content_hash="kubernetes-hash",
        ),
        KnowledgeChunk(
            chunk_id="career-planning",
            document_id=document.document_id,
            document_title=document.title,
            source=document.source,
            source_url=None,
            file_path=document.file_path,
            section="Career Planning",
            chunk_index=2,
            char_start=43,
            char_end=65,
            content="Prioritize career gaps.",
            content_hash="planning-hash",
        ),
    ]
    write_index(
        database_path,
        [document],
        chunks,
        [[0.0, 1.0], [1.0, 0.0], [0.6, 0.8]],
        embedding_model,
    )


def test_cosine_similarity_compares_vector_direction() -> None:
    assert cosine_similarity([1.0, 0.0], [2.0, 0.0]) == pytest.approx(1.0)
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)
    assert cosine_similarity([1.0, 0.0], [-1.0, 0.0]) == pytest.approx(-1.0)


def test_cosine_similarity_rejects_incompatible_vectors() -> None:
    with pytest.raises(ValueError, match="equal dimensions"):
        cosine_similarity([1.0], [1.0, 0.0])

    with pytest.raises(ValueError, match="zero vector"):
        cosine_similarity([0.0, 0.0], [1.0, 0.0])


def test_retrieve_chunks_ranks_results_and_respects_top_k(tmp_path: Path) -> None:
    database_path = tmp_path / "knowledge.db"
    _write_test_index(database_path)
    client = FakeOpenAIClient([1.0, 0.0])

    results = retrieve_chunks(
        "Kubernetes orchestration experience",
        database_path=database_path,
        top_k=2,
        client=client,
    )

    assert [result.rank for result in results] == [1, 2]
    assert [result.chunk_id for result in results] == [
        "container-orchestration",
        "career-planning",
    ]
    assert results[0].score == pytest.approx(1.0)
    assert results[1].score == pytest.approx(0.6)
    assert results[0].document_title == "Test Career Guide"
    assert results[0].section == "Container Orchestration"
    assert results[0].content == "Learn Kubernetes concepts."
    assert client.embeddings.calls == [
        {
            "model": EMBEDDING_MODEL,
            "input": ["Kubernetes orchestration experience"],
            "encoding_format": "float",
        }
    ]


def test_retrieve_chunks_rejects_an_index_from_another_model(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "knowledge.db"
    _write_test_index(database_path, embedding_model="another-model")
    client = FakeOpenAIClient([1.0, 0.0])

    with pytest.raises(ValueError, match="another-model"):
        retrieve_chunks("query", database_path=database_path, client=client)

    assert client.embeddings.calls == []


def test_retrieve_chunks_validates_query_and_top_k(tmp_path: Path) -> None:
    client = FakeOpenAIClient([1.0, 0.0])

    with pytest.raises(ValueError, match="must not be empty"):
        retrieve_chunks("  ", database_path=tmp_path / "missing.db", client=client)

    with pytest.raises(ValueError, match="at least 1"):
        retrieve_chunks(
            "query",
            database_path=tmp_path / "missing.db",
            top_k=0,
            client=client,
        )


def test_print_results_includes_required_fields(capsys) -> None:
    result = RetrievalResult(
        rank=1,
        score=0.875,
        document_title="Test Career Guide",
        section="Container Orchestration",
        chunk_id="container-orchestration",
        content="Learn Kubernetes concepts.",
    )

    print_results("Kubernetes", [result])

    output = capsys.readouterr().out
    assert "Rank: 1" in output
    assert "Cosine similarity: 0.875000" in output
    assert "Document: Test Career Guide" in output
    assert "Section: Container Orchestration" in output
    assert "Chunk ID: container-orchestration" in output
    assert "Learn Kubernetes concepts." in output
