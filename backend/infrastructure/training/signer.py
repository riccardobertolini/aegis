"""Model signer: SHA-256 hash + HMAC signature for trained model output.

Integrates with Phase 6 SecurityService when available.
Can work standalone (file-level SHA-256) without security engine.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_MANIFEST_FILENAME = "integrity.json"


class ModelSigner:
    """Signs a model directory with SHA-256 hashes + optional HMAC.

    Usage::

        signer = ModelSigner(hmac_secret=b"...")
        manifest = signer.sign(Path("models/my-finetuned"))
        ok = signer.verify(Path("models/my-finetuned"))
    """

    def __init__(self, hmac_secret: bytes | None = None) -> None:
        self._secret = hmac_secret

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def sign(self, model_dir: Path) -> dict:
        """Hash all files in model_dir and write integrity.json."""
        if not model_dir.is_dir():
            raise NotADirectoryError(f"Not a directory: {model_dir}")

        file_hashes: dict[str, str] = {}
        for p in sorted(model_dir.rglob("*")):
            if p.is_file() and p.name != _MANIFEST_FILENAME:
                rel = str(p.relative_to(model_dir))
                file_hashes[rel] = self._sha256(p)

        manifest: dict = {"files": file_hashes}
        if self._secret:
            manifest["hmac"] = self._hmac(file_hashes)

        manifest_path = model_dir / _MANIFEST_FILENAME
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        logger.info("Model signed: %s (%d files)", model_dir, len(file_hashes))
        return manifest

    def verify(self, model_dir: Path) -> bool:
        """Verify integrity.json against current file hashes."""
        manifest_path = model_dir / _MANIFEST_FILENAME
        if not manifest_path.exists():
            logger.warning("No integrity manifest found in %s", model_dir)
            return False

        with open(manifest_path) as f:
            manifest = json.load(f)

        expected: dict[str, str] = manifest.get("files", {})
        for rel, expected_hash in expected.items():
            p = model_dir / rel
            if not p.exists():
                logger.error("Missing file during verify: %s", rel)
                return False
            actual = self._sha256(p)
            if actual != expected_hash:
                logger.error("Hash mismatch: %s (expected %s, got %s)", rel, expected_hash, actual)
                return False

        if self._secret and "hmac" in manifest:
            expected_hmac = manifest["hmac"]
            actual_hmac = self._hmac(expected)
            if not hmac.compare_digest(expected_hmac, actual_hmac):
                logger.error("HMAC verification failed for %s", model_dir)
                return False

        logger.info("Model verified OK: %s", model_dir)
        return True

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    @staticmethod
    def _sha256(path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()

    def _hmac(self, file_hashes: dict[str, str]) -> str:
        payload = json.dumps(file_hashes, sort_keys=True).encode()
        return hmac.new(self._secret, payload, hashlib.sha256).hexdigest()
