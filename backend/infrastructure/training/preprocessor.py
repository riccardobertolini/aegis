"""Preprocessing: tokenization + chunking for SSM training.

Produces fixed-length token-id tensors ready for DataLoader.
Works with any tokenizer that exposes .encode(text) → ids.
"""
from __future__ import annotations

import logging
from typing import Any, Iterator

logger = logging.getLogger(__name__)


class Preprocessor:
    """Tokenise and pack text samples into fixed-length chunks.

    Parameters
    ----------
    tokenizer:
        Any object with ``encode(text)`` returning an object whose ``.ids``
        attribute is a list[int].  Compatible with HuggingFace tokenizers and
        the ``_ByteLevelFallbackTokenizer`` in inference/loader.py.
    max_length:
        Token window size fed to the SSM (default 512 for CPU; up to 2048 GPU).
    stride:
        Sliding-window overlap in tokens (default = max_length // 2).
    """

    def __init__(
        self,
        tokenizer: Any,
        max_length: int = 512,
        stride: int | None = None,
    ) -> None:
        self._tok = tokenizer
        self._max_length = max_length
        self._stride = stride if stride is not None else max_length // 2

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process_samples(
        self,
        texts: Iterator[str],
    ) -> list[list[int]]:
        """Tokenise all texts and return list of fixed-length chunks."""
        buffer: list[int] = []
        chunks: list[list[int]] = []

        for text in texts:
            ids = self._encode(text)
            buffer.extend(ids)
            while len(buffer) >= self._max_length:
                chunks.append(buffer[: self._max_length])
                buffer = buffer[self._stride :]

        # tail (pad if needed)
        if buffer:
            tail = buffer[: self._max_length]
            if len(tail) < self._max_length:
                tail = tail + [0] * (self._max_length - len(tail))
            chunks.append(tail)

        logger.info(
            "Preprocessor: %d chunks (max_length=%d, stride=%d)",
            len(chunks), self._max_length, self._stride,
        )
        return chunks

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _encode(self, text: str) -> list[int]:
        try:
            enc = self._tok.encode(text)
            return enc.ids if hasattr(enc, "ids") else list(enc)
        except Exception as exc:
            logger.warning("Tokenisation error (%s) — falling back to byte encoding", exc)
            return list(text.encode("utf-8"))
