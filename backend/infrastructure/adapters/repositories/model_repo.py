"""SQLite repository for AegisModel entities."""
from __future__ import annotations

from typing import List, Optional

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.domain.models import AegisModel
from backend.infrastructure.adapters.repositories.base_sqlite import BaseSQLiteRepository


class ModelRepository(BaseSQLiteRepository[AegisModel]):
    model = AegisModel

    async def find_active(self, session: AsyncSession) -> Optional[AegisModel]:
        result = await session.exec(
            select(AegisModel).where(AegisModel.is_active == True)  # noqa: E712
        )
        return result.first()

    async def find_by_architecture(
        self, architecture: str, session: AsyncSession
    ) -> List[AegisModel]:
        result = await session.exec(
            select(AegisModel).where(AegisModel.architecture == architecture)
        )
        return list(result.all())

    async def find_by_name(
        self, name: str, session: AsyncSession
    ) -> Optional[AegisModel]:
        result = await session.exec(select(AegisModel).where(AegisModel.name == name))
        return result.first()
