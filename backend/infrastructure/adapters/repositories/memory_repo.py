"""Concrete SQLite MemoryEntry repository."""
from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.entities.memory import MemoryEntry
from backend.domain.ports.repository import IMemoryEntryRepository
from backend.infrastructure.database.mappers import memory_to_orm, orm_to_memory
from backend.infrastructure.database.models import MemoryEntryModel
from .base_sqlite import BaseSQLiteRepository


class SQLiteMemoryEntryRepository(BaseSQLiteRepository[MemoryEntry, MemoryEntryModel], IMemoryEntryRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, MemoryEntryModel, memory_to_orm, orm_to_memory)

    async def list_by_session(self, session_id: str) -> list[MemoryEntry]:
        stmt = (
            select(MemoryEntryModel)
            .where(MemoryEntryModel.session_id == session_id)
            .order_by(MemoryEntryModel.created_at)
        )
        result = await self._session.execute(stmt)
        return [orm_to_memory(m) for m in result.scalars().all()]

    async def delete_by_session(self, session_id: str) -> int:
        stmt = delete(MemoryEntryModel).where(MemoryEntryModel.session_id == session_id)
        result = await self._session.execute(stmt)
        await self._session.commit()
        return result.rowcount
