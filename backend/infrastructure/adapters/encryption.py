"""Local Fernet-based encryption adapter (AES-128-CBC + HMAC-SHA256).

Keys are stored ONLY on local disk under data/keys/.
Never serialised to network. Air-gapped.

For AES-256-GCM strength use cryptography >= 41 and switch to AESGCM.
This implementation uses Fernet (safe default) with key versioning.
"""
from __future__ import annotations

import base64
import json
import os
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken, MultiFernet

from backend.domain.ports.encryption import IEncryptionPort
from backend.shared.exceptions import EncryptionError, KeyNotFoundError


class LocalEncryptionAdapter(IEncryptionPort):
    """Fernet symmetric encryption with local key store and rotation support."""

    KEY_FILE_NAME = "master.key"
    KEY_HISTORY_FILE = "key_history.json"

    def __init__(self, keys_dir: str | Path) -> None:
        self._keys_dir = Path(keys_dir)
        self._keys_dir.mkdir(parents=True, exist_ok=True)
        self._active_key_id, self._fernet = self._load_or_create_key()

    # ------------------------------------------------------------------
    # Key management
    # ------------------------------------------------------------------

    def _key_path(self, key_id: str) -> Path:
        return self._keys_dir / f"{key_id}.key"

    def _load_or_create_key(self) -> tuple[str, MultiFernet]:
        """Load existing active key or generate a new one."""
        index_path = self._keys_dir / "active_key_id.txt"
        if index_path.exists():
            key_id = index_path.read_text().strip()
            key_path = self._key_path(key_id)
            if not key_path.exists():
                raise KeyNotFoundError(f"Key file missing: {key_path}")
            raw = key_path.read_bytes()
            # Load history for MultiFernet (allows decrypting old ciphertexts)
            fernets = self._load_all_fernets(raw)
            return key_id, MultiFernet(fernets)
        else:
            return self._generate_new_key()

    def _generate_new_key(self) -> tuple[str, MultiFernet]:
        import uuid
        key_id = str(uuid.uuid4())
        raw = Fernet.generate_key()
        key_path = self._key_path(key_id)
        key_path.write_bytes(raw)
        key_path.chmod(0o600)
        (self._keys_dir / "active_key_id.txt").write_text(key_id)
        return key_id, MultiFernet([Fernet(raw)])

    def _load_all_fernets(self, active_raw: bytes) -> list[Fernet]:
        """Return [active, ...historical] Fernet instances for MultiFernet."""
        fernets = [Fernet(active_raw)]
        history_path = self._keys_dir / self.KEY_HISTORY_FILE
        if history_path.exists():
            history: list[str] = json.loads(history_path.read_text())
            for key_id in history:
                p = self._key_path(key_id)
                if p.exists():
                    fernets.append(Fernet(p.read_bytes()))
        return fernets

    # ------------------------------------------------------------------
    # IEncryptionPort
    # ------------------------------------------------------------------

    def encrypt_bytes(self, plaintext: bytes) -> bytes:
        try:
            return self._fernet.encrypt(plaintext)
        except Exception as exc:
            raise EncryptionError(f"encrypt_bytes failed: {exc}") from exc

    def decrypt_bytes(self, ciphertext: bytes) -> bytes:
        try:
            return self._fernet.decrypt(ciphertext)
        except InvalidToken as exc:
            raise EncryptionError("Decryption failed: invalid token or tampered data") from exc
        except Exception as exc:
            raise EncryptionError(f"decrypt_bytes failed: {exc}") from exc

    def encrypt_str(self, plaintext: str) -> str:
        return self.encrypt_bytes(plaintext.encode()).decode()

    def decrypt_str(self, ciphertext_b64: str) -> str:
        return self.decrypt_bytes(ciphertext_b64.encode()).decode()

    def rotate_key(self, old_ciphertext: bytes, new_key_id: str) -> bytes:
        """Decrypt with current key set, re-encrypt with fresh key."""
        plaintext = self.decrypt_bytes(old_ciphertext)
        new_key_path = self._key_path(new_key_id)
        if not new_key_path.exists():
            raise KeyNotFoundError(f"New key not found: {new_key_id}")
        new_fernet = Fernet(new_key_path.read_bytes())
        return new_fernet.encrypt(plaintext)

    def key_id(self) -> str:
        return self._active_key_id
