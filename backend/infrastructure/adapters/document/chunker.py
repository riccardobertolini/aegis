"""Text chunking pipeline with overlap and deduplication."""
from __future__ import annotations

import hashlib
import re
import uuid

from .models import ParsedDocument, TextChunk

_WHITESPACE_RE = re.compile(r"\s+")


def normalize_text(text: str) -> str:
    """Strip excessive whitespace, normalize Unicode."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # collapse multiple blank lines to one
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_text(
    doc: ParsedDocument,
    chunk_size: int = 512,
    overlap: int = 64,
    dedup: bool = True,
) -> list[TextChunk]:
    """
    Split *doc.raw_text* into overlapping chunks.

    Args:
        doc: Parsed document.
        chunk_size: Target size in characters.
        overlap: Overlap between consecutive chunks.
        dedup: Skip chunks with duplicate content hash.
    """
    text = normalize_text(doc.raw_text)
    if not text:
        return []

    document_id = hashlib.sha256(doc.source_path.encode()).hexdigest()[:16]
    chunks: list[TextChunk] = []
    seen_hashes: set[str] = set()
    start = 0
    index = 0
    step = max(1, chunk_size - overlap)

    # Pre-compute total so we can fill total_chunks later
    raw_chunks: list[tuple[int, int, str]] = []
    while start < len(text):
        end = min(start + chunk_size, len(text))
        snippet = text[start:end]
        raw_chunks.append((start, end, snippet))
        if end >= len(text):
            break
        start += step

    total = len(raw_chunks)
    for i, (s, e, snippet) in enumerate(raw_chunks):
        h = hashlib.sha256(snippet.encode()).hexdigest()
        if dedup and h in seen_hashes:
            continue
        seen_hashes.add(h)
        chunks.append(
            TextChunk(
                chunk_id=str(uuid.uuid4()),
                document_id=document_id,
                source_path=doc.source_path,
                text=snippet,
                chunk_index=index,
                total_chunks=total,
                start_char=s,
                end_char=e,
                metadata={
                    "format": doc.format,
                    "title": doc.title,
                    "author": doc.author,
                    **doc.metadata,
                },
            )
        )
        index += 1

    return chunks
