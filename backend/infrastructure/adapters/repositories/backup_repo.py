"""SQLite repository for BackupRecord entities."""
from __future__ import annotations

from typing import List

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.domain.models import BackupRecord
from backend.infrastructure.adapters.repositories.base_sqlite import BaseSQLiteRepository


class BackupRepository(BaseSQLiteRepository[BackupRecord]):
    model = BackupRecord

    async def find_by_type(
        self, backup_type: str, session: AsyncSession
    ) -> List[BackupRecord]:
        result = await session.exec(
            select(BackupRecord)
            .where(BackupRecord.backup_type == backup_type)
            .order_by(BackupRecord.created_at.desc())  # type: ignore[arg-type]
        )
        return list(result.all())

    async def find_latest(self, session: AsyncSession) -> BackupRecord | None:
        result = await session.exec(
            select(BackupRecord).order_by(BackupRecord.created_at.desc()).limit(1)  # type: ignore[arg-type]
        )
        return result.first()
