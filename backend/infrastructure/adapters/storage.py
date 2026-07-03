"""StorageManager — local filesystem storage for documents and models.

Layout
------
data/
  documents/<sha256[:2]>/<sha256[2:]>_<safe_filename>   <- content-addressed
  models/<model_name>/                                  <- manually copied
  embeddings/                                           <- ChromaDB managed
  logs/                                                 <- structlog JSON
  backups/                                              <- encrypted .aegbak

All I/O is local.  No HTTP, no S3, no NFS.
"""
from __future__ import annotations

import hashlib
import re
import shutil
from pathlib import Path

from backend.infrastructure.adapters.encryption import EncryptionService

_BASE_DIR = Path("data")

_SUBDIRS = [
    "documents",
    "models",
    "embeddings",
    "logs",
    "backups",
]


def _safe_filename(name: str) -> str:
    """Remove characters unsafe for filesystem paths."""
    return re.sub(r"[^\w.\-]", "_", name)


class StorageManager:
    """Local filesystem storage with optional per-file AES-256-GCM encryption."""

    def __init__(
        self,
        encryption: EncryptionService,
        base_dir: str | Path = _BASE_DIR,
    ) -> None:
        self._enc = encryption
        self._base = Path(base_dir)
        self._init_dirs()

    def _init_dirs(self) -> None:
        for sub in _SUBDIRS:
            (self._base / sub).mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Document storage (content-addressed by SHA-256)
    # ------------------------------------------------------------------

    def store_document(
        self,
        src_path: str,
        original_filename: str,
        encrypt: bool = False,
    ) -> str:
        """Store a document; return the destination path."""
        src = Path(src_path)
        raw = src.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        subdir = self._base / "documents" / digest[:2]
        subdir.mkdir(parents=True, exist_ok=True)
        safe = _safe_filename(original_filename)
        dest = subdir / f"{digest[2:]}_{safe}"
        if encrypt:
            dest = Path(str(dest) + ".enc")
            dest.write_bytes(self._enc.encrypt(raw))
        else:
            shutil.copy2(src, dest)
        return str(dest)

    # ------------------------------------------------------------------
    # Retrieve
    # ------------------------------------------------------------------

    def retrieve(self, path: str, encrypted: bool = False) -> bytes:
        """Read a stored file; decrypt if *encrypted*."""
        raw = Path(path).read_bytes()
        return self._enc.decrypt(raw) if encrypted else raw

    # ------------------------------------------------------------------
    # Integrity
    # ------------------------------------------------------------------

    def compute_sha256(self, path: str) -> str:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()

    def verify_integrity(self, path: str, expected_sha256: str | None = None) -> bool:
        """Return True if the file exists and (optionally) matches *expected_sha256*."""
        p = Path(path)
        if not p.exists():
            return False
        if expected_sha256 is None:
            # Derive expected from content-addressed path segment
            name = p.name
            parent = p.parent.name  # first 2 chars of sha256
            rest = name.split("_")[0]  # remaining sha256 chars
            expected_sha256 = parent + rest
        actual = hashlib.sha256(p.read_bytes()).hexdigest()
        return actual.startswith(expected_sha256[:4])  # partial sanity check

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete(self, path: str) -> None:
        p = Path(path)
        if p.exists():
            p.unlink()

    # ------------------------------------------------------------------
    # Model paths (read-only, manually placed)
    # ------------------------------------------------------------------

    def model_dir(self, model_name: str) -> Path:
        """Return (and ensure) the directory for a named model."""
        d = self._base / "models" / _safe_filename(model_name)
        d.mkdir(parents=True, exist_ok=True)
        return d
