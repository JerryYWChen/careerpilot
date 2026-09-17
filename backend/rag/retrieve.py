import argparse
import math
from collections.abc import Sequence
from pathlib import Path

from dotenv import load_dotenv

from backend.rag.embeddings import EMBEDDING_MODEL, generate_embeddings
from backend.rag.models import EmbeddedChunk, RetrievalResult
from backend.rag.store import load_embedded_chunks


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "careerpilot_knowledge.db"
DEFAULT_TOP_K = 3


def cosine_similarity(
    left: Sequence[float],
    right: Sequence[float],
) -> float:
    if not left or not right:
        raise ValueError("Cosine similarity requires non-empty vectors.")
    if len(left) != len(right):
        raise ValueError(
            "Cosine similarity requires vectors with equal dimensions: "
            f"got {len(left)} and {len(right)}."
        )

    left_norm = math.sqrt(math.fsum(value * value for value in left))
    right_norm = math.sqrt(math.fsum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        raise ValueError("Cosine similarity is undefined for a zero vector.")

    dot_product = math.fsum(
        left_value * right_value
        for left_value, right_value in zip(left, right, strict=True)
    )
    return dot_product / (left_norm * right_norm)


def _validate_index(chunks: list[EmbeddedChunk]) -> tuple[str, int]:
    if not chunks:
        raise ValueError("The knowledge index contains no chunks.")

    models = {chunk.embedding_model for chunk in chunks}
    if len(models) != 1:
        raise ValueError(
            "The knowledge index contains embeddings from multiple models: "
            f"{sorted(models)}. Rebuild the index with one model."
        )

    embedding_model = models.pop()
    if embedding_model != EMBEDDING_MODEL:
        raise ValueError(
            f"The knowledge index uses {embedding_model}, but retrieval is configured "
            f"for {EMBEDDING_MODEL}. Rebuild the index before searching."
        )

    dimensions = {chunk.embedding_dimensions for chunk in chunks}
    if len(dimensions) != 1:
        raise ValueError("The knowledge index contains mixed embedding dimensions.")

    embedding_dimensions = dimensions.pop()
    for chunk in chunks:
        if len(chunk.embedding) != embedding_dimensions:
            raise ValueError(
                f"Chunk {chunk.chunk_id} declares {embedding_dimensions} dimensions "
                f"but stores {len(chunk.embedding)} values."
            )

    return embedding_model, embedding_dimensions


def retrieve_chunks(
    query: str,
    *,
    database_path: Path = DEFAULT_DATABASE_PATH,
    top_k: int = DEFAULT_TOP_K,
    client=None,
) -> list[RetrievalResult]:
    if not query.strip():
        raise ValueError("The retrieval query must not be empty.")
    if top_k < 1:
        raise ValueError("top_k must be at least 1.")

    chunks = load_embedded_chunks(database_path)
    embedding_model, embedding_dimensions = _validate_index(chunks)
    query_embedding = generate_embeddings(
        [query],
        client=client,
        model=embedding_model,
    )[0]

    if len(query_embedding) != embedding_dimensions:
        raise ValueError(
            f"The query embedding has {len(query_embedding)} dimensions, but the "
            f"index uses {embedding_dimensions}."
        )

    ranked_chunks = sorted(
        (
            (cosine_similarity(query_embedding, chunk.embedding), chunk)
            for chunk in chunks
        ),
        key=lambda item: (-item[0], item[1].chunk_id),
    )[:top_k]

    return [
        RetrievalResult(
            rank=rank,
            score=score,
            chunk_id=chunk.chunk_id,
            document_title=chunk.document_title,
            section=chunk.section,
            content=chunk.content,
        )
        for rank, (score, chunk) in enumerate(ranked_chunks, start=1)
    ]


def print_results(query: str, results: list[RetrievalResult]) -> None:
    print(f"Query: {query}")
    print(f"Results: {len(results)}")

    for result in results:
        print(f"\nRank: {result.rank}")
        print(f"Cosine similarity: {result.score:.6f}")
        print(f"Document: {result.document_title}")
        print(f"Section: {result.section}")
        print(f"Chunk ID: {result.chunk_id}")
        print("Text:")
        print(result.content)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Search CareerPilot's local knowledge index by semantic similarity."
    )
    parser.add_argument("query", help="Text to search for.")
    parser.add_argument(
        "--top-k",
        type=int,
        default=DEFAULT_TOP_K,
        help=f"Number of ranked chunks to return (default: {DEFAULT_TOP_K}).",
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE_PATH,
        help="Path to the SQLite knowledge index.",
    )
    args = parser.parse_args()

    load_dotenv()
    results = retrieve_chunks(
        args.query,
        database_path=args.database,
        top_k=args.top_k,
    )
    print_results(args.query, results)


if __name__ == "__main__":
    main()
