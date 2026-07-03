"""Local embedding service — sentence-transformers (offline, no API calls)."""
from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Protocol

logger = logging.getLogger(__name__)


class IEmbedder(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...
    def dimension(self) -> int: ...


class SentenceTransformerEmbedder:
    """
    Wraps sentence-transformers for fully local embeddings.
    Model must be pre-downloaded and placed in models_dir.
    Default: all-MiniLM-L6-v2  (384 dims, 22 MB)
    """

    def __init__(self, model_name_or_path: str | Path = "all-MiniLM-L6-v2"):
        self._model_path = str(model_name_or_path)
        self._model = None
        self._lock = threading.Lock()

    def _load(self):
        with self._lock:
            if self._model is None:
                try:
                    from sentence_transformers import SentenceTransformer  # type: ignore
                    # local_files_only=True prevents any HTTP calls
                    self._model = SentenceTransformer(
                        self._model_path,
                        local_files_only=True,
                    )
                    logger.info("Embedder loaded: %s", self._model_path)
                except Exception as exc:
                    logger.error("Failed to load embedder %s: %s", self._model_path, exc)
                    raise

    def embed(self, texts: list[str]) -> list[list[float]]:
        self._load()
        vecs = self._model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
        return [v.tolist() for v in vecs]

    def dimension(self) -> int:
        self._load()
        return self._model.get_sentence_embedding_dimension()


class FallbackHashEmbedder:
    """
    Pure-Python deterministic embedder — no ML deps required.
    Used when sentence-transformers is not available.
    Produces 64-dim vectors from xxhash/hashlib; quality is low but functional
    for integration tests and CI environments without GPU/ML packages.
    """

    DIM = 64

    def embed(self, texts: list[str]) -> list[list[float]]:
        import hashlib
        result = []
        for text in texts:
            raw = hashlib.sha512(text.encode()).digest()  # 64 bytes
            floats = [b / 255.0 for b in raw]
            result.append(floats)
        return result

    def dimension(self) -> int:
        return self.DIM


def build_embedder(model_path: str | Path | None) -> IEmbedder:
    """Factory: try sentence-transformers, fall back to hash embedder."""
    if model_path:
        try:
            return SentenceTransformerEmbedder(model_path)
        except Exception as exc:
            logger.warning("SentenceTransformer unavailable (%s), using fallback.", exc)
    logger.warning("No embedding model configured — using FallbackHashEmbedder (low quality).")
    return FallbackHashEmbedder()
