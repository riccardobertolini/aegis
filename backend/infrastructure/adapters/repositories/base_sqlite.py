"""Base SQLite repository — common CRUD logic reused by all concrete repos."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Generic, Type, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

from backend.domain.entities.base import BaseEntity
from backend.domain.ports.repository import IRepository
from backend.shared.exceptions import EntityNotFoundError, RepositoryError

E = TypeVar("E", bound=BaseEntity)
M = TypeVar("M", bound=SQLModel)


class BaseSQLiteRepository(IRepository, Generic[E, M]):
    """Generic async SQLite repository over a SQLModel ORM model."""

    def __init__(
        self,
        session: AsyncSession,
        orm_class: Type[M],
        to_orm: Callable[[E], M],
        to_entity: Callable[[M], E],
    ) -> None:
        self._session = session
        self._orm_class = orm_class
        self._to_orm = to_orm
        self._to_entity = to_entity

    async def save(self, entity: E) -> E:
        try:
            entity.touch()
            orm_obj = self._to_orm(entity)
            merged = await self._session.merge(orm_obj)
            await self._session.commit()
            await self._session.refresh(merged)
            return self._to_entity(merged)
        except Exception as exc:
            await self._session.rollback()
            raise RepositoryError(f"save failed: {exc}") from exc

    async def get_by_id(self, entity_id: str) -> E | None:
        result = await self._session.get(self._orm_class, entity_id)
        return self._to_entity(result) if result else None

    async def list_all(self, limit: int = 100, offset: int = 0) -> list[E]:
        stmt = select(self._orm_class).offset(offset).limit(limit)
        result = await self._session.execute(stmt)
        return [self._to_entity(r) for r in result.scalars().all()]

    async def delete(self, entity_id: str) -> bool:
        obj = await self._session.get(self._orm_class, entity_id)
        if obj is None:
            return False
        await self._session.delete(obj)
        await self._session.commit()
        return True

    async def count(self) -> int:
        stmt = select(func.count()).select_from(self._orm_class)
        result = await self._session.execute(stmt)
        return result.scalar_one()
