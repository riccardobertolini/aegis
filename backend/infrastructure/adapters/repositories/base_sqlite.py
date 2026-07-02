"""BaseSQLiteRepository — generic async CRUD over SQLModel + aiosqlite.

All repositories extend this base.  The session is always injected
by the caller (FastAPI Depends or test fixture) — no hidden global state.

No remote DB, no cloud storage.  Everything is local SQLite.
"""
from __future__ import annotations

from typing import Generic, List, Optional, Type, TypeVar
from uuid import UUID

from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

T = TypeVar("T", bound=SQLModel)


class BaseSQLiteRepository(Generic[T]):
    """Provides create / find_by_id / find_all / update / delete for any SQLModel."""

    model: Type[T]

    async def create(self, entity: T, session: AsyncSession) -> T:
        session.add(entity)
        await session.commit()
        await session.refresh(entity)
        return entity

    async def find_by_id(self, entity_id: str | UUID, session: AsyncSession) -> Optional[T]:
        return await session.get(self.model, str(entity_id))

    async def find_all(
        self, session: AsyncSession, limit: int = 100, offset: int = 0
    ) -> List[T]:
        result = await session.exec(select(self.model).offset(offset).limit(limit))
        return list(result.all())

    async def update(self, entity: T, session: AsyncSession) -> T:
        session.add(entity)
        await session.commit()
        await session.refresh(entity)
        return entity

    async def delete(self, entity_id: str | UUID, session: AsyncSession) -> bool:
        entity = await self.find_by_id(entity_id, session)
        if entity is None:
            return False
        await session.delete(entity)
        await session.commit()
        return True
