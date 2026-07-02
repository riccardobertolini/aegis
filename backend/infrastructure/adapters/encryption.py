"""EncryptionService — AES-256-GCM local encryption.

All keys are stored exclusively on local disk (never transmitted).
Uses PyCA `cryptography` library — pure Python, zero native extensions
required beyond those bundled with the wheel.

Key lifecycle
-------------
1. On first instantiation a 256-bit key is generated with `os.urandom(32)`
   and written to `<key_dir>/aegis_master.key` (chmod 600).
2. Subsequent instantiations read the same file.
3. Key rotation: replace the file and re-encrypt all `_enc` columns
   (rotation utility to be implemented in a future administration phase).

Format
------
Every ciphertext is a raw bytes blob:
    [12 bytes nonce][16 bytes GCM tag][N bytes ciphertext]
Base64-encoded when stored as a string column.
"""
from __future__ import annotations

import base64
import os
import stat
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

_DEFAULT_KEY_DIR = Path("keys")
_KEY_FILENAME = "aegis_master.key"


class EncryptionService:
    """Local AES-256-GCM encryption / decryption service."""

    def __init__(self, key_dir: str | Path = _DEFAULT_KEY_DIR) -> None:
        self._key_dir = Path(key_dir)
        self._key_dir.mkdir(parents=True, exist_ok=True)
        self._key = self._load_or_create_key()
        self._aesgcm = AESGCM(self._key)

    # ------------------------------------------------------------------
    # Key management
    # ------------------------------------------------------------------

    def _key_path(self) -> Path:
        return self._key_dir / _KEY_FILENAME

    def _load_or_create_key(self) -> bytes:
        path = self._key_path()
        if path.exists():
            return path.read_bytes()
        key = os.urandom(32)  # 256-bit AES key
        path.write_bytes(key)
        # Restrict permissions to owner only (Unix)
        try:
            os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
        except NotImplementedError:
            pass  # Windows — best effort
        return key

    # ------------------------------------------------------------------
    # Core encrypt / decrypt (bytes)
    # ------------------------------------------------------------------

    def encrypt(self, plaintext: bytes) -> bytes:
        """Encrypt *plaintext* and return [nonce(12) | tag(16) | ciphertext]."""
        nonce = os.urandom(12)
        ciphertext_with_tag = self._aesgcm.encrypt(nonce, plaintext, None)
        return nonce + ciphertext_with_tag

    def decrypt(self, blob: bytes) -> bytes:
        """Decrypt a blob produced by :meth:`encrypt`."""
        nonce = blob[:12]
        ciphertext_with_tag = blob[12:]
        return self._aesgcm.decrypt(nonce, ciphertext_with_tag, None)

    # ------------------------------------------------------------------
    # String helpers (base64)
    # ------------------------------------------------------------------

    def encrypt_str(self, plaintext: str) -> str:
        """Encrypt a UTF-8 string; return base64-encoded ciphertext."""
        raw = self.encrypt(plaintext.encode("utf-8"))
        return base64.b64encode(raw).decode("ascii")

    def decrypt_str(self, encoded: str) -> str:
        """Decrypt a base64-encoded ciphertext back to UTF-8 string."""
        raw = base64.b64decode(encoded.encode("ascii"))
        return self.decrypt(raw).decode("utf-8")

    # ------------------------------------------------------------------
    # File helpers
    # ------------------------------------------------------------------

    def encrypt_file(self, src: str, dst: str) -> None:
        """Encrypt file at *src* and write ciphertext to *dst*."""
        plaintext = Path(src).read_bytes()
        Path(dst).write_bytes(self.encrypt(plaintext))

    def decrypt_file(self, src: str, dst: str) -> None:
        """Decrypt file at *src* (ciphertext) and write plaintext to *dst*."""
        blob = Path(src).read_bytes()
        Path(dst).write_bytes(self.decrypt(blob))
