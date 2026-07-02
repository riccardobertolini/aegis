"""Local filesystem storage adapter.

All files stored under a configured base_dir.
Optionally encrypted at rest using IEncryptionPort.
No cloud, no network. Air-gapped.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from backend.domain.ports.encryption import IEncryptionPort
from backend.domain.ports.storage import IStoragePort
from backend.shared.exceptions import ChecksumMismatchError, StorageError


class LocalStorageAdapter(IStoragePort):
    """Stores files on local disk; optionally wraps writes/reads with IEncryptionPort."""

    ENCRYPTED_SUFFIX = ".enc"

    def __init__(self, base_dir: str | Path, encryption: IEncryptionPort | None = None) -> None:
        self._base = Path(base_dir).resolve()
        self._base.mkdir(parents=True, exist_ok=True)
        self._enc = encryption

    def _resolve(self, relative_path: str) -> Path:
        full = (self._base / relative_path).resolve()
        if not str(full).startswith(str(self._base)):
            raise StorageError("Path traversal attempt detected")
        return full

    def save(self, relative_path: str, data: bytes, encrypt: bool = True) -> str:
        try:
            if encrypt and self._enc:
                data = self._enc.encrypt_bytes(data)
                if not relative_path.endswith(self.ENCRYPTED_SUFFIX):
                    relative_path += self.ENCRYPTED_SUFFIX
            path = self._resolve(relative_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            return relative_path
        except StorageError:
            raise
        except Exception as exc:
            raise StorageError(f"save failed [{relative_path}]: {exc}") from exc

    def load(self, relative_path: str) -> bytes:
        try:
            path = self._resolve(relative_path)
            if not path.exists():
                # try with .enc suffix
                enc_path = self._resolve(relative_path + self.ENCRYPTED_SUFFIX)
                if enc_path.exists():
                    path = enc_path
                else:
                    raise StorageError(f"File not found: {relative_path}")
            raw = path.read_bytes()
            if self._enc and str(path).endswith(self.ENCRYPTED_SUFFIX):
                return self._enc.decrypt_bytes(raw)
            return raw
        except StorageError:
            raise
        except Exception as exc:
            raise StorageError(f"load failed [{relative_path}]: {exc}") from exc

    def delete(self, relative_path: str) -> bool:
        for suffix in ("", self.ENCRYPTED_SUFFIX):
            p = self._resolve(relative_path + suffix)
            if p.exists():
                p.unlink()
                return True
        return False

    def exists(self, relative_path: str) -> bool:
        return (
            self._resolve(relative_path).exists()
            or self._resolve(relative_path + self.ENCRYPTED_SUFFIX).exists()
        )

    def checksum_sha256(self, relative_path: str) -> str:
        for suffix in ("", self.ENCRYPTED_SUFFIX):
            p = self._resolve(relative_path + suffix)
            if p.exists():
                return hashlib.sha256(p.read_bytes()).hexdigest()
        raise StorageError(f"File not found for checksum: {relative_path}")

    def list_files(self, subdir: str = "") -> list[str]:
        root = self._resolve(subdir) if subdir else self._base
        if not root.exists():
            return []
        return [
            str(p.relative_to(self._base))
            for p in root.rglob("*")
            if p.is_file()
        ]

    def absolute_path(self, relative_path: str) -> Path:
        return self._resolve(relative_path)
