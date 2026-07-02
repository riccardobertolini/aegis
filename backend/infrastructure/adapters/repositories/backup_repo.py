"""Concrete SQLite Backup repository."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.entities.backup import Backup, BackupStatus
from backend.domain.ports.repository import IBackupRepository
from backend.infrastructure.database.mappers import backup_to_orm, orm_to_backup
from backend.infrastructure.database.models import BackupModel
from .base_sqlite import BaseSQLiteRepository


class SQLiteBackupRepository(BaseSQLiteRepository[Backup, BackupModel], IBackupRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, BackupModel, backup_to_orm, orm_to_backup)

    async def list_completed(self) -> list[Backup]:
        stmt = (
            select(BackupModel)
            .where(BackupModel.status == BackupStatus.COMPLETED.value)
            .order_by(BackupModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return [orm_to_backup(m) for m in result.scalars().all()]

    async def get_latest(self) -> Backup | None:
        stmt = (
            select(BackupModel)
            .where(BackupModel.status == BackupStatus.COMPLETED.value)
            .order_by(BackupModel.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        return orm_to_backup(m) if m else None
