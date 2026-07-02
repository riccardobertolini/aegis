"""SQLite repository for AuditLog entries (append-only WORM pattern)."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlmodel import select

from backend.infrastructure.adapters.repositories.base_sqlite import BaseSQLiteRepository
from backend.infrastructure.database.models import AuditLogModel


class SQLiteAuditLogRepository(BaseSQLiteRepository[AuditLogModel]):
    model = AuditLogModel

    # Audit logs are APPEND-ONLY: override delete/update to prevent misuse.
    async def update(self, entity: AuditLogModel) -> AuditLogModel:  # type: ignore[override]
        raise NotImplementedError("Audit log entries are immutable.")

    async def delete(self, entity_id: str) -> bool:  # type: ignore[override]
        raise NotImplementedError("Audit log entries cannot be deleted.")

    async def find_by_actor(self, actor_id: str, limit: int = 200) -> List[AuditLogModel]:
        result = await self._session.exec(
            select(AuditLogModel)
            .where(AuditLogModel.actor_id == actor_id)
            .order_by(AuditLogModel.created_at.desc())  # type: ignore[attr-defined]
            .limit(limit)
        )
        return list(result.all())

    async def find_by_resource(
        self, resource_type: str, resource_id: Optional[str] = None, limit: int = 200
    ) -> List[AuditLogModel]:
        stmt = (
            select(AuditLogModel)
            .where(AuditLogModel.resource_type == resource_type)
            .order_by(AuditLogModel.created_at.desc())  # type: ignore[attr-defined]
            .limit(limit)
        )
        if resource_id:
            stmt = stmt.where(AuditLogModel.resource_id == resource_id)
        result = await self._session.exec(stmt)
        return list(result.all())

    async def find_in_range(
        self, since: datetime, until: datetime, limit: int = 1000
    ) -> List[AuditLogModel]:
        result = await self._session.exec(
            select(AuditLogModel)
            .where(
                AuditLogModel.created_at >= since,
                AuditLogModel.created_at <= until,
            )
            .order_by(AuditLogModel.created_at.asc())  # type: ignore[attr-defined]
            .limit(limit)
        )
        return list(result.all())


AuditLogRepository = SQLiteAuditLogRepository
