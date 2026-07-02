"""ModelSigner — SHA-256 integrity + HMAC-SHA256 signature for model files.

Security contract:
- Every model file gets a SHA-256 hash stored in metadata.json.
- The metadata block itself is signed with HMAC-SHA256 using a local secret key
  from the encrypted vault (never stored in .env or source code).
- At load time, the InferenceEngine calls verify_integrity() before weights
  are mapped into memory. A tampered checkpoint is rejected before execution.

No network calls. All cryptographic operations are local.
"""
from __future__ import annotations

import hashlib
import hmac
import json
from pathlib import Path

import structlog

log = structlog.get_logger(__name__)

_CHUNK_SIZE = 8 * 1024 * 1024  # 8 MB


class ModelSigner:
    """
    Provides file hashing and HMAC-based metadata signing.

    Args:
        secret_key: bytes secret used for HMAC signing of metadata.
                    Loaded from the local vault — never from env vars in production.
    """

    def __init__(self, secret_key: bytes) -> None:
        self._secret_key = secret_key

    # ------------------------------------------------------------------
    # File hashing
    # ------------------------------------------------------------------

    @staticmethod
    def hash_file(path: Path) -> str:
        """
        Compute SHA-256 of a file in streaming chunks (handles large model files).

        Returns hex-encoded digest string.
        """
        sha256 = hashlib.sha256()
        with open(path, "rb") as fh:
            while chunk := fh.read(_CHUNK_SIZE):
                sha256.update(chunk)
        return sha256.hexdigest()

    def verify_file(self, path: Path, expected_hash: str) -> bool:
        """
        Return True if the file's SHA-256 matches *expected_hash*.

        An empty *expected_hash* (model not yet registered) returns False.
        """
        if not expected_hash:
            log.warning("model.hash_missing", path=str(path))
            return False
        if not path.exists():
            log.error("model.file_missing", path=str(path))
            return False
        actual = self.hash_file(path)
        match = hmac.compare_digest(actual, expected_hash)
        if not match:
            log.error(
                "model.hash_mismatch",
                path=str(path),
                expected=expected_hash[:16] + "...",
                actual=actual[:16] + "...",
            )
        return match

    # ------------------------------------------------------------------
    # Metadata signing
    # ------------------------------------------------------------------

    def sign_metadata(self, metadata_dict: dict) -> str:
        """
        Compute HMAC-SHA256 over a canonical JSON serialisation of metadata_dict.

        The *signature* field itself is excluded from the signed payload.
        Returns hex-encoded HMAC digest.
        """
        payload = {k: v for k, v in metadata_dict.items() if k != "signature"}
        canonical = json.dumps(payload, sort_keys=True, ensure_ascii=True)
        digest = hmac.new(self._secret_key, canonical.encode(), hashlib.sha256)
        return digest.hexdigest()

    def verify_metadata(self, metadata_dict: dict) -> bool:
        """
        Verify the *signature* field inside metadata_dict.

        Returns True if the signature is valid.
        """
        expected = metadata_dict.get("signature", "")
        if not expected:
            log.warning("model.metadata_unsigned")
            return False
        actual = self.sign_metadata(metadata_dict)
        return hmac.compare_digest(actual, expected)
