"""SQLite repository for Workflow entities."""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.domain.models import Workflow
from backend.infrastructure.adapters.repositories.base_sqlite import BaseSQLiteRepository


class WorkflowRepository(BaseSQLiteRepository[Workflow]):
    model = Workflow

    async def find_by_assistant(
        self, assistant_id: UUID, session: AsyncSession
    ) -> List[Workflow]:
        result = await session.exec(
            select(Workflow).where(Workflow.assistant_id == str(assistant_id))
        )
        return list(result.all())

    async def find_active(self, session: AsyncSession) -> List[Workflow]:
        result = await session.exec(
            select(Workflow).where(Workflow.is_active == True)  # noqa: E712
        )
        return list(result.all())

    async def find_by_name(
        self, name: str, session: AsyncSession
    ) -> Optional[Workflow]:
        result = await session.exec(select(Workflow).where(Workflow.name == name))
        return result.first()
