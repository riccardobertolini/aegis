"""Backup manager port."""
from __future__ import annotations

from abc import ABC, abstractmethod

from backend.domain.entities.backup import Backup


class IBackupManagerPort(ABC):
    """Port for creating and restoring local encrypted backups."""

    @abstractmethod
    async def create_backup(
        self,
        label: str,
        includes: list[str],
        initiated_by: str,
    ) -> Backup:
        """Create a full or partial encrypted backup; return Backup record."""

    @abstractmethod
    async def restore_backup(self, backup_id: str) -> None:
        """Restore system state from a backup (offline only)."""

    @abstractmethod
    async def verify_backup(self, backup_id: str) -> bool:
        """Verify backup integrity via checksum; return True if intact."""

    @abstractmethod
    async def list_backups(self) -> list[Backup]:
        """List all available backups."""

    @abstractmethod
    async def delete_backup(self, backup_id: str) -> bool:
        """Delete a backup file and record."""
