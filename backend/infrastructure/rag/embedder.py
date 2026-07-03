"""LocalEmbedder — local sentence-transformers embedder.

Completely offline. Models must be present locally.
Default model: all-MiniLM-L6-v2 (384-dim, ~22 MB, Apache-2.0).
Any sentence-transformers compatible model can be substituted.
"""
from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

# Dimensions for the default model
_DEFAULT_MODEL = "all-MiniLM-L6-v2"
_DEFAULT_DIM = 384


class LocalEmbedder:
    """Wraps sentence-transformers SentenceTransformer for offline use.

    The model is loaded from a local path (``models_root/embed/<model_name>``).
    If the path does not exist but the model name matches a known HuggingFace
    model AND the system is online, it will NOT download automatically —
    this is intentional (air-gapped constraint).

    To pre-download for offline use (one-time, on an internet-connected machine)::

        python -m backend.infrastructure.rag.embedder --download all-MiniLM-L6-v2

    Then copy ``models/embed/<model_name>/`` to the air-gapped machine.
    """

    def __init__(
        self,
        model_name_or_path: str = _DEFAULT_MODEL,
        models_root: str | Path | None = None,
        device: str | None = None,  # None = auto-detect
        batch_size: int = 64,
        normalize_embeddings: bool = True,
    ) -> None:
        self._model_name = model_name_or_path
        self._models_root = Path(models_root) if models_root else None
        self._device = device
        self._batch_size = batch_size
        self._normalize = normalize_embeddings
        self._model = None  # lazy-loaded
        self._executor = None  # use asyncio default thread pool

    @property
    def dimension(self) -> int:
        """Embedding dimension. Returns default until model is loaded."""
        if self._model is not None:
            try:
                return self._model.get_sentence_embedding_dimension()
            except Exception:
                pass
        return _DEFAULT_DIM

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of strings. Returns list of float vectors."""
        if not texts:
            return []
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            self._embed_sync,
            texts,
        )

    async def embed_query(self, text: str) -> list[float]:
        """Embed a single query string."""
        results = await self.embed_texts([text])
        return results[0] if results else []

    def load(self) -> None:
        """Explicitly load the model (optional — lazy-loaded on first use)."""
        self._ensure_loaded()

    # ------------------------------------------------------------------
    # Sync internals (run in thread pool)
    # ------------------------------------------------------------------

    def _embed_sync(self, texts: list[str]) -> list[list[float]]:
        self._ensure_loaded()
        embeddings = self._model.encode(  # type: ignore[union-attr]
            texts,
            batch_size=self._batch_size,
            normalize_embeddings=self._normalize,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        return [e.tolist() for e in embeddings]

    def _ensure_loaded(self) -> None:
        if self._model is not None:
            return
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
        except ImportError as exc:
            raise ImportError(
                "sentence-transformers is required for local embeddings. "
                "Add it to requirements/ml.txt."
            ) from exc

        # Resolve local path
        model_path = self._resolve_model_path()

        # Block automatic download — set HF_HUB_OFFLINE env var
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

        device = self._device or self._auto_device()
        logger.info("Loading embedder from '%s' on %s", model_path, device)
        self._model = SentenceTransformer(
            model_name_or_path=str(model_path),
            device=device,
        )
        logger.info(
            "Embedder ready — dim=%d device=%s",
            self.dimension,
            device,
        )

    def _resolve_model_path(self) -> Path | str:
        """Prefer local path; fall back to model name (for pre-cached HF cache)."""
        if self._models_root is not None:
            local = self._models_root / "embed" / self._model_name
            if local.exists():
                return local
            logger.warning(
                "Embed model not found at %s — using name '%s' "
                "(must be in HF cache; no download will occur)",
                local,
                self._model_name,
            )
        return self._model_name

    @staticmethod
    def _auto_device() -> str:
        try:
            import torch
            return "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            return "cpu"


# ---------------------------------------------------------------------------
# CLI helper for pre-downloading (run on internet-connected machine only)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Pre-download an embedding model for offline use"
    )
    parser.add_argument("model_name", help="e.g. all-MiniLM-L6-v2")
    parser.add_argument("--out", default="models/embed", help="Output directory")
    args = parser.parse_args()

    from sentence_transformers import SentenceTransformer  # type: ignore

    out_path = Path(args.out) / args.model_name
    out_path.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {args.model_name} → {out_path}")
    m = SentenceTransformer(args.model_name)
    m.save(str(out_path))
    print("Done. Copy models/embed/ to the air-gapped machine.")
