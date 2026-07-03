"""AES-256-GCM symmetric encryption for data at rest — fully local.

Key material is stored in an encrypted keystore file on disk,
never in the database.

Keystore layout (JSON, encrypted with master key derived from passphrase):
{
  "active_key_id": "<kid>",
  "keys": {
    "<kid>": {"key_b64": "<base64-AES-256>", "created_at": "<iso>"}
  }
}

Master key derivation: PBKDF2-HMAC-SHA256, 600_000 iterations, salt in keystore header.
"""
import base64
import json
import secrets
from datetime import datetime
from pathlib import Path

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

_NONCE_BYTES = 12
_KEY_BYTES = 32  # AES-256


# ─── Key derivation ────────────────────────────────────────────────────────────

def _derive_master_key(passphrase: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=_KEY_BYTES,
        salt=salt,
        iterations=600_000,
    )
    return kdf.derive(passphrase.encode())


# ─── Keystore ─────────────────────────────────────────────────────────────────

class LocalKeyStore:
    """Manages AES-256-GCM keys stored in an encrypted local file."""

    def __init__(self, keystore_path: str, passphrase: str) -> None:
        self._path = Path(keystore_path)
        self._passphrase = passphrase
        self._keystore: dict = {"active_key_id": "", "keys": {}}
        self._master_key: bytes | None = None
        self._salt: bytes | None = None
        self._load_or_init()

    # ── persistence ──

    def _load_or_init(self) -> None:
        if self._path.exists():
            raw = self._path.read_bytes()
            # First 16 bytes = salt, rest = encrypted JSON
            self._salt = raw[:16]
            self._master_key = _derive_master_key(self._passphrase, self._salt)
            nonce = raw[16:28]
            ciphertext = raw[28:]
            aesgcm = AESGCM(self._master_key)
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            self._keystore = json.loads(plaintext.decode())
        else:
            self._salt = secrets.token_bytes(16)
            self._master_key = _derive_master_key(self._passphrase, self._salt)
            self._keystore = {"active_key_id": "", "keys": {}}
            self._rotate_key_internal()
            self._save()

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        plaintext = json.dumps(self._keystore).encode()
        nonce = secrets.token_bytes(_NONCE_BYTES)
        aesgcm = AESGCM(self._master_key)  # type: ignore[arg-type]
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)
        self._path.write_bytes(self._salt + nonce + ciphertext)  # type: ignore[operator]
        # Restrict permissions: owner read/write only
        self._path.chmod(0o600)

    # ── key management ──

    def _rotate_key_internal(self) -> str:
        kid = secrets.token_hex(8)
        raw_key = secrets.token_bytes(_KEY_BYTES)
        self._keystore["keys"][kid] = {
            "key_b64": base64.b64encode(raw_key).decode(),
            "created_at": datetime.utcnow().isoformat(),
        }
        self._keystore["active_key_id"] = kid
        return kid

    def rotate(self) -> str:
        kid = self._rotate_key_internal()
        self._save()
        return kid

    def _active_key(self) -> bytes:
        kid = self._keystore["active_key_id"]
        return base64.b64decode(self._keystore["keys"][kid]["key_b64"])

    def _key_by_id(self, kid: str) -> bytes:
        entry = self._keystore["keys"].get(kid)
        if entry is None:
            raise KeyError(f"Unknown key id: {kid}")
        return base64.b64decode(entry["key_b64"])

    def active_key_id(self) -> str:
        return self._keystore["active_key_id"]

    # ── encryption / decryption ──

    def encrypt(self, plaintext: bytes) -> bytes:
        """Returns: kid(8 hex) + nonce(12) + ciphertext."""
        kid = self._keystore["active_key_id"]
        key = self._active_key()
        nonce = secrets.token_bytes(_NONCE_BYTES)
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)
        return kid.encode() + nonce + ciphertext  # 8 + 12 + len(ct)

    def decrypt(self, blob: bytes) -> bytes:
        """Parses kid prefix, selects correct key, decrypts."""
        kid = blob[:16].decode(errors="replace").rstrip()  # 8-char hex = 16 bytes ASCII? no: token_hex(8) = 16 chars
        # kid is token_hex(8) = 16 hex chars
        kid = blob[:16].decode()
        nonce = blob[16:28]
        ciphertext = blob[28:]
        key = self._key_by_id(kid)
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, ciphertext, None)
