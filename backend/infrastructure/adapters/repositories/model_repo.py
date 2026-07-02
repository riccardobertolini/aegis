"""Concrete SQLite ModelRecord and Dataset repositories."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.entities.model import Dataset, ModelRecord, ModelStatus
from backend.domain.ports.repository import IDatasetRepository, IModelRecordRepository
from backend.infrastructure.database.mappers import dataset_to_orm, model_to_orm, orm_to_dataset, orm_to_model
from backend.infrastructure.database.models import DatasetModel, ModelRecordModel
from .base_sqlite import BaseSQLiteRepository


class SQLiteModelRecordRepository(BaseSQLiteRepository[ModelRecord, ModelRecordModel], IModelRecordRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, ModelRecordModel, model_to_orm, orm_to_model)

    async def get_by_name(self, name: str) -> ModelRecord | None:
        stmt = select(ModelRecordModel).where(ModelRecordModel.name == name)
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        return orm_to_model(m) if m else None

    async def list_available(self) -> list[ModelRecord]:
        stmt = select(ModelRecordModel).where(ModelRecordModel.status == ModelStatus.AVAILABLE.value)
        result = await self._session.execute(stmt)
        return [orm_to_model(m) for m in result.scalars().all()]


class SQLiteDatasetRepository(BaseSQLiteRepository[Dataset, DatasetModel], IDatasetRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, DatasetModel, dataset_to_orm, orm_to_dataset)

    async def list_by_owner(self, owner_id: str) -> list[Dataset]:
        stmt = select(DatasetModel).where(DatasetModel.owner_id == owner_id)
        result = await self._session.execute(stmt)
        return [orm_to_dataset(m) for m in result.scalars().all()]
