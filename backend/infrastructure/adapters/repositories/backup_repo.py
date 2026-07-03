"""SQLite repository for Backup records."""
from __future__ import annotations

from sqlmodel import select

from backend.infrastructure.adapters.repositories.base_sqlite import BaseSQLiteRepository
from backend.infrastructure.database.models import BackupModel


class SQLiteBackupRepository(BaseSQLiteRepository[BackupModel]):
    model = BackupModel

    async def find_by_status(self, status: str) -> list[BackupModel]:
        result = await self._session.exec(
            select(BackupModel)
            .where(BackupModel.status == status)
            .order_by(BackupModel.created_at.desc())  # type: ignore[attr-defined]
        )
        return list(result.all())

    async def find_latest(self, n: int = 10) -> list[BackupModel]:
        result = await self._session.exec(
            select(BackupModel)
            .order_by(BackupModel.created_at.desc())  # type: ignore[attr-defined]
            .limit(n)
        )
        return list(result.all())

    async def find_by_label(self, label: str) -> BackupModel | None:
        result = await self._session.exec(
            select(BackupModel).where(BackupModel.label == label)
        )
        return result.first()


BackupRepository = SQLiteBackupRepository
