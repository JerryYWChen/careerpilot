import argparse
import hashlib
import json
from pathlib import Path

from dotenv import load_dotenv

from backend.rag.chunking import chunk_document
from backend.rag.embeddings import EMBEDDING_MODEL, generate_embeddings
from backend.rag.models import KnowledgeChunk, KnowledgeDocument
from backend.rag.store import inspect_index, write_index


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_KNOWLEDGE_DIR = PROJECT_ROOT / "knowledge"
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "careerpilot_knowledge.db"


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def load_documents_and_chunks(
    knowledge_dir: Path,
) -> tuple[list[KnowledgeDocument], list[KnowledgeChunk]]:
    manifest_path = knowledge_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    if not isinstance(manifest, list):
        raise ValueError("Knowledge manifest must contain a JSON list.")

    documents: list[KnowledgeDocument] = []
    chunks: list[KnowledgeChunk] = []
    document_ids: set[str] = set()
    resolved_knowledge_dir = knowledge_dir.resolve()

    for entry in manifest:
        document_id = entry["id"]
        if document_id in document_ids:
            raise ValueError(f"Duplicate document id: {document_id}")
        document_ids.add(document_id)

        relative_path = Path(entry["path"])
        document_path = (knowledge_dir / relative_path).resolve()
        if not document_path.is_relative_to(resolved_knowledge_dir):
            raise ValueError(f"Document path leaves the knowledge directory: {relative_path}")

        markdown = document_path.read_text(encoding="utf-8")
        document = KnowledgeDocument(
            document_id=document_id,
            title=entry["title"],
            source=entry["source"],
            source_url=entry.get("source_url"),
            file_path=relative_path.as_posix(),
            content_hash=_hash_text(markdown),
        )
        document_chunks = chunk_document(document, markdown)

        if not document_chunks:
            raise ValueError(f"Document produced no chunks: {relative_path}")

        documents.append(document)
        chunks.extend(document_chunks)

    return documents, chunks


def build_index(
    knowledge_dir: Path = DEFAULT_KNOWLEDGE_DIR,
    database_path: Path = DEFAULT_DATABASE_PATH,
    *,
    client=None,
) -> tuple[int, int]:
    documents, chunks = load_documents_and_chunks(knowledge_dir)
    embeddings = generate_embeddings(
        [chunk.content for chunk in chunks],
        client=client,
        model=EMBEDDING_MODEL,
    )
    write_index(
        database_path,
        documents,
        chunks,
        embeddings,
        EMBEDDING_MODEL,
    )
    return len(documents), len(chunks)


def print_chunks(chunks: list[KnowledgeChunk]) -> None:
    for chunk in chunks:
        print(
            f"\n[{chunk.document_id} / {chunk.section} / chunk {chunk.chunk_index}]"
        )
        print(
            f"id={chunk.chunk_id[:12]}... chars={chunk.char_start}:{chunk.char_end} "
            f"hash={chunk.content_hash[:12]}..."
        )
        print(chunk.content)


def print_index(database_path: Path) -> None:
    documents, chunks = inspect_index(database_path)
    print(f"Database: {database_path}")
    print(f"Stored documents: {len(documents)}")
    print(f"Stored chunks: {len(chunks)}")

    for document in documents:
        print(f"\nDocument: {document['document_id']} - {document['title']}")
        print(
            f"source={document['source']} "
            f"source_url={document['source_url'] or 'None'} "
            f"file={document['file_path']} "
            f"hash={document['content_hash'][:12]}..."
        )

    for row in chunks:
        print(
            f"\n[{row['document_id']} / {row['section']} / "
            f"chunk {row['chunk_index']}]"
        )
        print(
            f"id={row['chunk_id'][:12]}... "
            f"chars={row['char_start']}:{row['char_end']} "
            f"hash={row['content_hash'][:12]}... "
            f"model={row['embedding_model']} "
            f"dimensions={row['embedding_dimensions']}"
        )
        print(row["content"])


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build or inspect CareerPilot's local knowledge index."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Read and chunk documents without generating embeddings.",
    )
    mode.add_argument(
        "--inspect",
        action="store_true",
        help="Print chunks and vector metadata stored in SQLite.",
    )
    parser.add_argument(
        "--knowledge-dir",
        type=Path,
        default=DEFAULT_KNOWLEDGE_DIR,
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=DEFAULT_DATABASE_PATH,
    )
    args = parser.parse_args()

    if args.inspect:
        print_index(args.database)
        return

    if args.dry_run:
        documents, chunks = load_documents_and_chunks(args.knowledge_dir)
        print(f"Documents: {len(documents)}")
        print(f"Chunks: {len(chunks)}")
        print_chunks(chunks)
        return

    load_dotenv()
    document_count, chunk_count = build_index(
        args.knowledge_dir,
        args.database,
    )
    print(
        f"Indexed {document_count} documents and {chunk_count} chunks "
        f"into {args.database} using {EMBEDDING_MODEL}."
    )


if __name__ == "__main__":
    main()
