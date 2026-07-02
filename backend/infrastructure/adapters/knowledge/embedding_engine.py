"""Local embedding engine using sentence-transformers (100% offline).

Model files MUST be copied manually into models/embeddings/<model_name>/
before use. No automatic download is performed.
"""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from backend.shared.logging import get_logger

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)

_DEFAULT_MODEL_DIR = Path("models/embeddings/all-MiniLM-L6-v2")


class EmbeddingEngine:
    """
    Wraps sentence-transformers SentenceTransformer for local embedding.

    Air-gapped usage:
        1. On an internet-connected machine:
               python -m sentence_transformers download all-MiniLM-L6-v2 --cache-dir ./tmp
           Then copy ./tmp/<model_id>/ → models/embeddings/all-MiniLM-L6-v2/
        2. Set AEGIS_EMBEDDING_MODEL_DIR in .env to the local path.
        3. The engine loads from disk — zero HTTP calls.
    """

    def __init__(self, model_dir: str | Path = _DEFAULT_MODEL_DIR) -> None:
        self._model_dir = Path(model_dir)
        self._model = None  # lazy load

    def _load(self) -> None:
        if self._model is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer

            logger.info("embedding.model.loading", path=str(self._model_dir))
            self._model = SentenceTransformer(str(self._model_dir), local_files_only=True)
            logger.info("embedding.model.loaded", path=str(self._model_dir))
        except ImportError as exc:
            raise RuntimeError(
                "sentence-transformers is not installed. "
                "Add it to requirements/ml.txt and install offline."
            ) from exc
        except Exception as exc:
            raise RuntimeError(
                f"Failed to load embedding model from {self._model_dir}: {exc}. "
                "Ensure model files are present (see docs/architecture/offline_setup.md)."
            ) from exc

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return dense embeddings for *texts*. Shape: (N, D)."""
        self._load()
        vectors = self._model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return vectors.tolist()

    def embed_one(self, text: str) -> list[float]:
        """Convenience wrapper for single text."""
        return self.embed([text])[0]

    @property
    def model_dir(self) -> Path:
        return self._model_dir
