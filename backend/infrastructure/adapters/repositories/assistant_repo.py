"""SQLite repository for Assistant entities."""
from __future__ import annotations

from sqlmodel import select

from backend.infrastructure.adapters.repositories.base_sqlite import BaseSQLiteRepository
from backend.infrastructure.database.models import AssistantModel


class SQLiteAssistantRepository(BaseSQLiteRepository[AssistantModel]):
    model = AssistantModel

    async def find_by_owner(self, owner_id: str) -> list[AssistantModel]:
        result = await self._session.exec(
            select(AssistantModel).where(AssistantModel.owner_id == owner_id)
        )
        return list(result.all())

    async def find_active_by_owner(self, owner_id: str) -> list[AssistantModel]:
        result = await self._session.exec(
            select(AssistantModel)
            .where(AssistantModel.owner_id == owner_id, AssistantModel.is_active == True)  # noqa: E712
        )
        return list(result.all())

    async def find_by_name(self, name: str, owner_id: str) -> AssistantModel | None:
        result = await self._session.exec(
            select(AssistantModel)
            .where(AssistantModel.name == name, AssistantModel.owner_id == owner_id)
        )
        return result.first()


AssistantRepository = SQLiteAssistantRepository
