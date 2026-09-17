import hashlib
import re

from backend.rag.models import KnowledgeChunk, KnowledgeDocument


DEFAULT_MAX_CHARS = 1000
DEFAULT_OVERLAP_CHARS = 150
_HEADING_PATTERN = re.compile(r"^#{1,6}\s+(.+?)\s*$")


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _markdown_sections(markdown: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []
    heading = "Introduction"
    body_lines: list[str] = []

    def add_section() -> None:
        body = " ".join(" ".join(body_lines).split())
        if body:
            sections.append((heading, body))

    for line in markdown.splitlines():
        match = _HEADING_PATTERN.match(line.strip())

        if match:
            add_section()
            heading = match.group(1).strip()
            body_lines = []
        else:
            body_lines.append(line)

    add_section()
    return sections


def _section_windows(
    text: str,
    max_chars: int,
    overlap_chars: int,
) -> list[tuple[int, int, str]]:
    windows: list[tuple[int, int, str]] = []
    start = 0

    while start < len(text):
        end = min(start + max_chars, len(text))

        if end < len(text):
            boundary = text.rfind(" ", start + max_chars // 2, end + 1)
            if boundary > start:
                end = boundary

        content = text[start:end].strip()
        if content:
            windows.append((start, end, content))

        if end == len(text):
            break

        next_start = max(0, end - overlap_chars)

        while next_start < end and next_start > 0 and not text[next_start - 1].isspace():
            next_start += 1

        while next_start < len(text) and text[next_start].isspace():
            next_start += 1

        if next_start <= start:
            next_start = end

        start = next_start

    return windows


def chunk_document(
    document: KnowledgeDocument,
    markdown: str,
    max_chars: int = DEFAULT_MAX_CHARS,
    overlap_chars: int = DEFAULT_OVERLAP_CHARS,
) -> list[KnowledgeChunk]:
    if max_chars <= 0:
        raise ValueError("max_chars must be greater than zero.")

    if overlap_chars < 0 or overlap_chars >= max_chars:
        raise ValueError("overlap_chars must be between zero and max_chars.")

    chunks: list[KnowledgeChunk] = []

    for section, section_text in _markdown_sections(markdown):
        for char_start, char_end, content in _section_windows(
            section_text,
            max_chars,
            overlap_chars,
        ):
            chunk_index = len(chunks)
            content_hash = _hash_text(content)
            chunk_id = _hash_text(
                f"{document.document_id}:{chunk_index}:{content_hash}"
            )
            chunks.append(
                KnowledgeChunk(
                    chunk_id=chunk_id,
                    document_id=document.document_id,
                    document_title=document.title,
                    source=document.source,
                    source_url=document.source_url,
                    file_path=document.file_path,
                    section=section,
                    chunk_index=chunk_index,
                    char_start=char_start,
                    char_end=char_end,
                    content=content,
                    content_hash=content_hash,
                )
            )

    return chunks

