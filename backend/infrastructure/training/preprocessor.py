"""Text preprocessor — tokenisation + batching for SSM training."""
from __future__ import annotations

import logging
from typing import Any, Iterator

logger = logging.getLogger(__name__)


class TextPreprocessor:
    """
    Converts raw text samples to token-id tensors for SSM/Mamba training.
    Works with any tokenizer that exposes `.encode(text).ids`.
    Falls back to UTF-8 byte encoding when no tokenizer is available.
    """

    def __init__(self, tokenizer: Any, max_seq_len: int = 512) -> None:
        self._tok = tokenizer
        self._max_seq_len = max_seq_len

    def tokenize(self, texts: list[str]) -> list[list[int]]:
        result: list[list[int]] = []
        for text in texts:
            ids = self._encode(text)
            # sliding-window chunking with 50% overlap
            if len(ids) <= self._max_seq_len:
                result.append(ids)
            else:
                step = self._max_seq_len // 2
                for start in range(0, len(ids) - self._max_seq_len + 1, step):
                    result.append(ids[start : start + self._max_seq_len])
                # last partial chunk
                tail = ids[-(self._max_seq_len):]
                if tail not in result:
                    result.append(tail)
        return result

    def make_batches(
        self, token_sequences: list[list[int]], batch_size: int
    ) -> Iterator[list[list[int]]]:
        for i in range(0, len(token_sequences), batch_size):
            yield token_sequences[i : i + batch_size]

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _encode(self, text: str) -> list[int]:
        try:
            enc = self._tok.encode(text)
            return enc.ids if hasattr(enc, "ids") else list(enc)
        except Exception:
            return list(text.encode("utf-8"))
