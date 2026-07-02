"""SQLite repository for Assistant entities."""
from __future__ import annotations

from typing import List, Optional

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.domain.models import Assistant
from backend.infrastructure.adapters.repositories.base_sqlite import BaseSQLiteRepository


class AssistantRepository(BaseSQLiteRepository[Assistant]):
    model = Assistant

    async def find_by_name(self, name: str, session: AsyncSession) -> Optional[Assistant]:
        result = await session.exec(select(Assistant).where(Assistant.name == name))
        return result.first()

    async def find_active(self, session: AsyncSession) -> List[Assistant]:
        result = await session.exec(select(Assistant).where(Assistant.is_active == True))  # noqa: E712
        return list(result.all())

    async def find_by_owner(self, owner_id: str, session: AsyncSession) -> List[Assistant]:
        result = await session.exec(select(Assistant).where(Assistant.owner_id == owner_id))
        return list(result.all())
