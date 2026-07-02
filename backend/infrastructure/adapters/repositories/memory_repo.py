"""SQLite repository for MemoryChunk entities."""
from __future__ import annotations

from typing import List
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.domain.models import MemoryChunk
from backend.infrastructure.adapters.repositories.base_sqlite import BaseSQLiteRepository


class MemoryRepository(BaseSQLiteRepository[MemoryChunk]):
    model = MemoryChunk

    async def find_by_assistant(
        self, assistant_id: UUID, session: AsyncSession
    ) -> List[MemoryChunk]:
        result = await session.exec(
            select(MemoryChunk)
            .where(MemoryChunk.assistant_id == str(assistant_id))
            .order_by(MemoryChunk.importance.desc())  # type: ignore[arg-type]
        )
        return list(result.all())

    async def find_by_user(
        self, user_id: UUID, session: AsyncSession
    ) -> List[MemoryChunk]:
        result = await session.exec(
            select(MemoryChunk).where(MemoryChunk.user_id == str(user_id))
        )
        return list(result.all())
