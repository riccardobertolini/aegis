"""BaseSQLiteRepository — generic async CRUD over SQLModel + aiosqlite.

All domain repositories extend this base.  The AsyncSession is always
injected by the caller (FastAPI Depends or test fixture); no hidden
global state, fully SOLID-compliant.

Air-gapped: only local SQLite, no remote DB.
"""
from __future__ import annotations

import builtins
from typing import Generic, TypeVar
from uuid import UUID

from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

T = TypeVar("T", bound=SQLModel)


class BaseSQLiteRepository(Generic[T]):
    """Generic async CRUD: create / get / list / update / delete."""

    model: type[T]

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, entity: T) -> T:
        self._session.add(entity)
        await self._session.commit()
        await self._session.refresh(entity)
        return entity

    async def get(self, entity_id: str | UUID) -> T | None:
        return await self._session.get(self.model, str(entity_id))

    # Kept for backwards-compat with old callers that pass session explicitly
    async def find_by_id(self, entity_id: str | UUID, session: AsyncSession | None = None) -> T | None:
        sess = session or self._session
        return await sess.get(self.model, str(entity_id))

    async def list(self, limit: int = 100, offset: int = 0) -> builtins.list[T]:
        result = await self._session.exec(
            select(self.model).offset(offset).limit(limit)
        )
        return list(result.all())

    async def update(self, entity: T) -> T:
        self._session.add(entity)
        await self._session.commit()
        await self._session.refresh(entity)
        return entity

    async def delete(self, entity_id: str | UUID) -> bool:
        entity = await self.get(entity_id)
        if entity is None:
            return False
        await self._session.delete(entity)
        await self._session.commit()
        return True
