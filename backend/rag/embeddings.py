from collections.abc import Sequence

from openai import OpenAI


EMBEDDING_MODEL = "text-embedding-3-small"


def generate_embeddings(
    texts: Sequence[str],
    *,
    client: OpenAI | None = None,
    model: str = EMBEDDING_MODEL,
) -> list[list[float]]:
    if not texts:
        return []

    if any(not text.strip() for text in texts):
        raise ValueError("Embedding inputs must not be empty.")

    embedding_client = client or OpenAI()
    response = embedding_client.embeddings.create(
        model=model,
        input=list(texts),
        encoding_format="float",
    )
    ordered_data = sorted(response.data, key=lambda item: item.index)

    expected_indices = list(range(len(texts)))
    actual_indices = [item.index for item in ordered_data]
    if actual_indices != expected_indices:
        raise ValueError(
            "Embedding response indices did not match the input order: "
            f"expected {expected_indices}, got {actual_indices}."
        )

    embeddings = [list(item.embedding) for item in ordered_data]
    dimensions = {len(embedding) for embedding in embeddings}
    if 0 in dimensions or len(dimensions) != 1:
        raise ValueError("Embedding vectors must be non-empty and have equal dimensions.")

    return embeddings
