"""Concrete SQLite Assistant repository."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.entities.assistant import Assistant
from backend.domain.ports.repository import IAssistantRepository
from backend.infrastructure.database.mappers import assistant_to_orm, orm_to_assistant
from backend.infrastructure.database.models import AssistantModel
from .base_sqlite import BaseSQLiteRepository


class SQLiteAssistantRepository(BaseSQLiteRepository[Assistant, AssistantModel], IAssistantRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AssistantModel, assistant_to_orm, orm_to_assistant)

    async def list_by_owner(self, owner_id: str) -> list[Assistant]:
        stmt = select(AssistantModel).where(AssistantModel.owner_id == owner_id)
        result = await self._session.execute(stmt)
        return [orm_to_assistant(m) for m in result.scalars().all()]

    async def get_active(self) -> list[Assistant]:
        stmt = select(AssistantModel).where(AssistantModel.is_active == True)  # noqa: E712
        result = await self._session.execute(stmt)
        return [orm_to_assistant(m) for m in result.scalars().all()]
