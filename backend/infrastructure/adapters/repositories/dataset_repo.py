"""SQLite repository for Dataset entities."""
from __future__ import annotations

from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.domain.models import Dataset
from backend.infrastructure.adapters.repositories.base_sqlite import BaseSQLiteRepository


class DatasetRepository(BaseSQLiteRepository[Dataset]):
    """Concrete repository for Dataset."""

    model = Dataset

    async def find_by_model(
        self, model_id: UUID, session: AsyncSession
    ) -> list[Dataset]:
        result = await session.exec(
            select(Dataset).where(Dataset.model_id == model_id)
        )
        return list(result.all())

    async def find_by_status(
        self, status: str, session: AsyncSession
    ) -> list[Dataset]:
        result = await session.exec(
            select(Dataset).where(Dataset.status == status)
        )
        return list(result.all())
