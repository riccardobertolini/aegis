"""TextChunker — sliding-window chunking with sentence-boundary awareness.

Splits a list of raw text blocks into fixed-size overlapping chunks
suitable for embedding and vector storage.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class Chunk:
    text: str
    chunk_index: int
    document_id: str
    metadata: dict = field(default_factory=dict)


class TextChunker:
    """Sliding-window text chunker.

    Args:
        chunk_size:    Target number of characters per chunk.
        chunk_overlap: Number of characters to repeat at the start of each
                       subsequent chunk (context window overlap).
        min_chunk_len: Chunks shorter than this are dropped.
    """

    # Sentence boundary pattern: end of sentence followed by whitespace
    _SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 64,
        min_chunk_len: int = 32,
    ) -> None:
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._min_chunk_len = min_chunk_len

    def chunk_document(
        self,
        document_id: str,
        blocks: list[str],
        base_metadata: dict | None = None,
    ) -> list[Chunk]:
        """Chunk all text blocks of a document."""
        full_text = " ".join(b.strip() for b in blocks if b.strip())
        return self._sliding_window(document_id, full_text, base_metadata or {})

    def chunk_text(
        self,
        document_id: str,
        text: str,
        base_metadata: dict | None = None,
    ) -> list[Chunk]:
        """Chunk a single text string."""
        return self._sliding_window(document_id, text, base_metadata or {})

    # ------------------------------------------------------------------
    # Core algorithm
    # ------------------------------------------------------------------

    def _sliding_window(self, document_id: str, text: str, meta: dict) -> list[Chunk]:
        sentences = self._SENT_SPLIT.split(text)
        chunks: list[Chunk] = []
        current: list[str] = []
        current_len = 0
        chunk_idx = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            slen = len(sentence)

            # If a single sentence exceeds chunk_size, hard-split it
            if slen > self._chunk_size:
                # Flush current buffer first
                if current_len >= self._min_chunk_len:
                    chunks.append(self._make_chunk(document_id, chunk_idx, " ".join(current), meta))
                    chunk_idx += 1
                current, current_len = [], 0

                for start in range(0, slen, self._chunk_size - self._chunk_overlap):
                    piece = sentence[start: start + self._chunk_size]
                    if len(piece) >= self._min_chunk_len:
                        chunks.append(self._make_chunk(document_id, chunk_idx, piece, meta))
                        chunk_idx += 1
                continue

            # Would overflow? Flush and start new chunk with overlap
            if current_len + slen + 1 > self._chunk_size and current:
                chunk_text = " ".join(current)
                if len(chunk_text) >= self._min_chunk_len:
                    chunks.append(self._make_chunk(document_id, chunk_idx, chunk_text, meta))
                    chunk_idx += 1

                # Overlap: keep last N chars worth of sentences
                overlap_buf: list[str] = []
                overlap_len = 0
                for s in reversed(current):
                    if overlap_len + len(s) + 1 > self._chunk_overlap:
                        break
                    overlap_buf.insert(0, s)
                    overlap_len += len(s) + 1
                current = overlap_buf
                current_len = overlap_len

            current.append(sentence)
            current_len += slen + 1

        # Flush remainder
        if current:
            chunk_text = " ".join(current)
            if len(chunk_text) >= self._min_chunk_len:
                chunks.append(self._make_chunk(document_id, chunk_idx, chunk_text, meta))

        return chunks

    @staticmethod
    def _make_chunk(document_id: str, idx: int, text: str, meta: dict) -> Chunk:
        return Chunk(
            text=text,
            chunk_index=idx,
            document_id=document_id,
            metadata={**meta, "chunk_index": idx},
        )
