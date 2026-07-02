"""Local encrypted backup manager.

Creates tar.gz archives of selected data directories,
encrypts them at rest, stores checksum for integrity verification.
No network. Air-gapped.
"""
from __future__ import annotations

import hashlib
import io
import shutil
import tarfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

from backend.domain.entities.backup import Backup, BackupStatus
from backend.domain.ports.backup_manager import IBackupManagerPort
from backend.domain.ports.encryption import IEncryptionPort
from backend.domain.ports.repository import IBackupRepository
from backend.shared.exceptions import BackupError, RestoreError


class LocalBackupManager(IBackupManagerPort):
    """Creates encrypted tar.gz backups of local data dirs."""

    def __init__(
        self,
        backup_dir: str | Path,
        data_dir: str | Path,
        encryption: IEncryptionPort,
        backup_repo: IBackupRepository,
    ) -> None:
        self._backup_dir = Path(backup_dir)
        self._data_dir = Path(data_dir)
        self._backup_dir.mkdir(parents=True, exist_ok=True)
        self._enc = encryption
        self._repo = backup_repo

    # ------------------------------------------------------------------
    # IBackupManagerPort
    # ------------------------------------------------------------------

    async def create_backup(self, label: str, includes: list[str], initiated_by: str) -> Backup:
        backup_id = str(uuid.uuid4())
        archive_name = f"{backup_id}.tar.gz.enc"
        archive_path = self._backup_dir / archive_name
        record = Backup()
        record.id = backup_id
        record.label = label
        record.storage_path = str(archive_path)
        record.includes = includes
        record.initiated_by = initiated_by
        record.status = BackupStatus.IN_PROGRESS
        await self._repo.save(record)
        try:
            buf = io.BytesIO()
            with tarfile.open(fileobj=buf, mode="w:gz") as tar:
                for component in includes:
                    src = self._data_dir / component
                    if src.exists():
                        tar.add(src, arcname=component)
            compressed = buf.getvalue()
            encrypted = self._enc.encrypt_bytes(compressed)
            archive_path.write_bytes(encrypted)
            checksum = hashlib.sha256(encrypted).hexdigest()
            record.status = BackupStatus.COMPLETED
            record.checksum_sha256 = checksum
            record.size_bytes = len(encrypted)
        except Exception as exc:
            record.status = BackupStatus.FAILED
            record.error_message = str(exc)
            await self._repo.save(record)
            raise BackupError(f"Backup creation failed: {exc}") from exc
        return await self._repo.save(record)

    async def restore_backup(self, backup_id: str) -> None:
        record = await self._repo.get_by_id(backup_id)
        if record is None:
            raise RestoreError(f"Backup not found: {backup_id}")
        if record.status != BackupStatus.COMPLETED:
            raise RestoreError(f"Backup {backup_id} is not in COMPLETED state")
        try:
            encrypted = Path(record.storage_path).read_bytes()
            if not await self.verify_backup(backup_id):
                raise RestoreError("Checksum mismatch — backup may be corrupted")
            compressed = self._enc.decrypt_bytes(encrypted)
            buf = io.BytesIO(compressed)
            with tarfile.open(fileobj=buf, mode="r:gz") as tar:
                tar.extractall(self._data_dir)  # noqa: S202
        except RestoreError:
            raise
        except Exception as exc:
            raise RestoreError(f"Restore failed: {exc}") from exc

    async def verify_backup(self, backup_id: str) -> bool:
        record = await self._repo.get_by_id(backup_id)
        if record is None:
            return False
        try:
            raw = Path(record.storage_path).read_bytes()
            actual = hashlib.sha256(raw).hexdigest()
            return actual == record.checksum_sha256
        except Exception:
            return False

    async def list_backups(self) -> list[Backup]:
        return await self._repo.list_all(limit=1000)

    async def delete_backup(self, backup_id: str) -> bool:
        record = await self._repo.get_by_id(backup_id)
        if record is None:
            return False
        Path(record.storage_path).unlink(missing_ok=True)
        return await self._repo.delete(backup_id)
