"""SQLite repositories for ModelRecord and Dataset entities."""
from __future__ import annotations

from typing import List, Optional

from sqlmodel import select

from backend.infrastructure.adapters.repositories.base_sqlite import BaseSQLiteRepository
from backend.infrastructure.database.models import DatasetModel, ModelRecordModel


class SQLiteModelRecordRepository(BaseSQLiteRepository[ModelRecordModel]):
    model = ModelRecordModel

    async def find_by_name(self, name: str) -> Optional[ModelRecordModel]:
        result = await self._session.exec(
            select(ModelRecordModel).where(ModelRecordModel.name == name)
        )
        return result.first()

    async def find_by_status(self, status: str) -> List[ModelRecordModel]:
        result = await self._session.exec(
            select(ModelRecordModel).where(ModelRecordModel.status == status)
        )
        return list(result.all())

    async def find_available(self) -> List[ModelRecordModel]:
        return await self.find_by_status("available")


ModelRecordRepository = SQLiteModelRecordRepository


class SQLiteDatasetRepository(BaseSQLiteRepository[DatasetModel]):
    model = DatasetModel

    async def find_by_owner(self, owner_id: str) -> List[DatasetModel]:
        result = await self._session.exec(
            select(DatasetModel).where(DatasetModel.owner_id == owner_id)
        )
        return list(result.all())

    async def find_by_name(self, name: str, owner_id: str) -> Optional[DatasetModel]:
        result = await self._session.exec(
            select(DatasetModel)
            .where(DatasetModel.name == name, DatasetModel.owner_id == owner_id)
        )
        return result.first()


DatasetRepository = SQLiteDatasetRepository
