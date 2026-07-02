"""SQLite repository for MemoryEntry entities."""
from __future__ import annotations

from typing import List

from sqlmodel import select

from backend.infrastructure.adapters.repositories.base_sqlite import BaseSQLiteRepository
from backend.infrastructure.database.models import MemoryEntryModel


class SQLiteMemoryEntryRepository(BaseSQLiteRepository[MemoryEntryModel]):
    model = MemoryEntryModel

    async def find_by_session(self, session_id: str, limit: int = 200) -> List[MemoryEntryModel]:
        result = await self._session.exec(
            select(MemoryEntryModel)
            .where(MemoryEntryModel.session_id == session_id)
            .order_by(MemoryEntryModel.created_at)  # type: ignore[arg-type]
            .limit(limit)
        )
        return list(result.all())

    async def find_by_assistant(self, assistant_id: str, limit: int = 500) -> List[MemoryEntryModel]:
        result = await self._session.exec(
            select(MemoryEntryModel)
            .where(MemoryEntryModel.assistant_id == assistant_id)
            .order_by(MemoryEntryModel.created_at)  # type: ignore[arg-type]
            .limit(limit)
        )
        return list(result.all())

    async def find_by_user(self, user_id: str, limit: int = 500) -> List[MemoryEntryModel]:
        result = await self._session.exec(
            select(MemoryEntryModel)
            .where(MemoryEntryModel.user_id == user_id)
            .order_by(MemoryEntryModel.created_at)  # type: ignore[arg-type]
            .limit(limit)
        )
        return list(result.all())

    async def delete_by_session(self, session_id: str) -> int:
        """Delete all entries for a session. Returns count deleted."""
        entries = await self.find_by_session(session_id, limit=10_000)
        for entry in entries:
            await self._session.delete(entry)
        await self._session.commit()
        return len(entries)


MemoryEntryRepository = SQLiteMemoryEntryRepository
