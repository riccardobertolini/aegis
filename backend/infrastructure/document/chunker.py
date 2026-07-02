"""Local text chunker — recursive split, no external dependencies."""
from __future__ import annotations

from backend.domain.ports.document import ChunkingConfig


class TextChunker:
    """Recursive character-based splitter à-la LangChain, but self-contained."""

    _SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, config: ChunkingConfig | None = None):
        self.config = config or ChunkingConfig()

    def split(self, text: str) -> list[str]:
        if not text.strip():
            return []
        return self._split_recursive(text, self._SEPARATORS)

    def _split_recursive(self, text: str, separators: list[str]) -> list[str]:
        sep = separators[0] if separators else ""
        splits = text.split(sep) if sep else list(text)

        chunks: list[str] = []
        current: list[str] = []
        current_len = 0

        for s in splits:
            s_len = len(s)
            if current_len + s_len + len(sep) > self.config.chunk_size and current:
                merged = sep.join(current).strip()
                if merged:
                    chunks.append(merged)
                # Keep overlap
                overlap_tokens: list[str] = []
                overlap_len = 0
                for t in reversed(current):
                    if overlap_len + len(t) <= self.config.chunk_overlap:
                        overlap_tokens.insert(0, t)
                        overlap_len += len(t)
                    else:
                        break
                current = overlap_tokens
                current_len = overlap_len

            current.append(s)
            current_len += s_len + len(sep)

        if current:
            merged = sep.join(current).strip()
            if merged:
                chunks.append(merged)

        # If a chunk is still too large and we have a finer separator, recurse
        if len(separators) > 1:
            refined: list[str] = []
            for chunk in chunks:
                if len(chunk) > self.config.chunk_size:
                    refined.extend(self._split_recursive(chunk, separators[1:]))
                else:
                    refined.append(chunk)
            return refined

        return chunks
