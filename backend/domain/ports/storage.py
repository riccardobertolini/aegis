"""Local file storage port."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class IStoragePort(ABC):
    """Port for local filesystem operations on binary assets.

    All paths are relative to a configured base_dir.
    No cloud, no network. Air-gapped.
    """

    @abstractmethod
    def save(self, relative_path: str, data: bytes, encrypt: bool = True) -> str:
        """Write data to disk; return actual relative path stored."""

    @abstractmethod
    def load(self, relative_path: str) -> bytes:
        """Read and (if encrypted) decrypt file contents."""

    @abstractmethod
    def delete(self, relative_path: str) -> bool:
        """Delete file; return True if existed."""

    @abstractmethod
    def exists(self, relative_path: str) -> bool:
        """Return True if file exists on disk."""

    @abstractmethod
    def checksum_sha256(self, relative_path: str) -> str:
        """Compute SHA-256 hex digest of stored (raw, pre-decrypt) bytes."""

    @abstractmethod
    def list_files(self, subdir: str = "") -> list[str]:
        """Return relative paths of all files under subdir."""

    @abstractmethod
    def absolute_path(self, relative_path: str) -> Path:
        """Resolve to absolute Path (for FFI / subprocess callers)."""
