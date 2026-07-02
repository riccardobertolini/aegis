"""ModelRegistry — scans the models/ directory and maintains metadata.

Design:
- On startup, scans AEGIS_MODELS_DIR for subdirectories containing metadata.json.
- Verifies SHA-256 of checkpoint and tokenizer files against stored hashes.
- Provides CRUD over the in-memory registry (no network, no auto-download).
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import structlog

from backend.domain.model.model_metadata import ModelMetadata, ModelVersion, QuantizationLevel
from backend.shared.exceptions import ModelNotFoundError
from backend.infrastructure.adapters.inference.model_signer import ModelSigner

log = structlog.get_logger(__name__)


class ModelRegistry:
    """
    Scans and indexes locally stored Mamba/SSM models.

    Thread-safe for reads; writes use an asyncio.Lock in the service layer.
    """

    def __init__(self, models_dir: Path, signer: ModelSigner) -> None:
        self._models_dir = models_dir
        self._signer = signer
        self._registry: dict[str, ModelMetadata] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def scan(self) -> list[ModelMetadata]:
        """Scan models_dir and refresh the in-memory registry. Returns all found models."""
        found: list[ModelMetadata] = []
        if not self._models_dir.exists():
            log.warning("models_dir.missing", path=str(self._models_dir))
            return found

        for candidate in sorted(self._models_dir.iterdir()):
            if not candidate.is_dir():
                continue
            meta_path = candidate / "metadata.json"
            if not meta_path.exists():
                log.debug("model.no_metadata", path=str(candidate))
                continue
            try:
                meta = self._load_metadata(meta_path)
                self._registry[meta.model_id] = meta
                found.append(meta)
                log.info("model.registered", model_id=meta.model_id, version=str(meta.version))
            except Exception as exc:
                log.error("model.registration_failed", path=str(candidate), error=str(exc))

        return found

    def get(self, model_id: str) -> ModelMetadata:
        """Return metadata for *model_id* or raise ModelNotFoundError."""
        if model_id not in self._registry:
            raise ModelNotFoundError(
                f"Model '{model_id}' not found in registry.",
                model_id=model_id,
            )
        return self._registry[model_id]

    def list_all(self) -> list[ModelMetadata]:
        """Return all registered models."""
        return list(self._registry.values())

    def register(self, meta: ModelMetadata) -> None:
        """Manually register a model (used after manual copy to models_dir)."""
        self._registry[meta.model_id] = meta
        log.info("model.manually_registered", model_id=meta.model_id)

    def verify_integrity(self, model_id: str) -> bool:
        """
        Re-verify SHA-256 hashes of checkpoint and tokenizer files.

        Returns True if all hashes match, False otherwise.
        """
        meta = self.get(model_id)
        ckpt_ok = self._signer.verify_file(
            meta.checkpoint_path(self._models_dir),
            meta.sha256_checkpoint,
        )
        tok_ok = self._signer.verify_file(
            meta.tokenizer_path(self._models_dir),
            meta.sha256_tokenizer,
        )
        ok = ckpt_ok and tok_ok
        log.info(
            "model.integrity_check",
            model_id=model_id,
            checkpoint_ok=ckpt_ok,
            tokenizer_ok=tok_ok,
            result="pass" if ok else "FAIL",
        )
        return ok

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _load_metadata(path: Path) -> ModelMetadata:
        raw = json.loads(path.read_text(encoding="utf-8"))
        version_str = raw.pop("version", "1.0.0")
        quant_str = raw.pop("quantization", "none")
        created_str = raw.pop("created_at", None)
        return ModelMetadata(
            version=ModelVersion.from_string(version_str),
            quantization=QuantizationLevel(quant_str),
            created_at=datetime.fromisoformat(created_str) if created_str else datetime.utcnow(),
            **raw,
        )
