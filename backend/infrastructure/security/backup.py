"""Encrypted backup / restore using AES-256-GCM.

Format: [4-byte magic][16-byte salt][12-byte nonce][ciphertext]
The backup key is derived from the keystore passphrase + a separate backup salt.
"""
import hashlib
import secrets
import shutil
import tarfile
from pathlib import Path
from datetime import datetime

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

_MAGIC = b"AEGB"  # Aegis Encrypted Backup
_KEY_BYTES = 32
_ITERATIONS = 600_000


def _derive_backup_key(passphrase: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=_KEY_BYTES,
        salt=salt,
        iterations=_ITERATIONS,
    )
    return kdf.derive(passphrase.encode())


class BackupService:
    def __init__(self, passphrase: str) -> None:
        self._passphrase = passphrase

    def create(self, source_path: str, dest_path: str) -> str:
        """Tar + encrypt source_path → dest_path.  Returns backup filename."""
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        tar_path = Path(dest_path) / f"aegis_backup_{timestamp}.tar"
        final_path = tar_path.with_suffix(".aeb")  # Aegis Encrypted Backup

        # 1. Create tar archive
        with tarfile.open(tar_path, "w") as tar:
            tar.add(source_path, arcname="backup")

        # 2. Encrypt
        salt = secrets.token_bytes(16)
        nonce = secrets.token_bytes(12)
        key = _derive_backup_key(self._passphrase, salt)
        aesgcm = AESGCM(key)
        plaintext = tar_path.read_bytes()
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)

        final_path.write_bytes(_MAGIC + salt + nonce + ciphertext)
        final_path.chmod(0o600)
        tar_path.unlink()  # Remove unencrypted tar
        return str(final_path)

    def restore(self, backup_path: str, dest_path: str) -> None:
        """Decrypt + untar backup_path → dest_path."""
        raw = Path(backup_path).read_bytes()
        if raw[:4] != _MAGIC:
            raise ValueError("Not a valid Aegis backup file")
        salt = raw[4:20]
        nonce = raw[20:32]
        ciphertext = raw[32:]
        key = _derive_backup_key(self._passphrase, salt)
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)

        tmp_tar = Path(dest_path) / "_restore_tmp.tar"
        tmp_tar.write_bytes(plaintext)
        with tarfile.open(tmp_tar) as tar:
            tar.extractall(dest_path)
        tmp_tar.unlink()
