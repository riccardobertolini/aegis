"""Concrete SQLite AuditLog repository."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.entities.audit import AuditLog
from backend.domain.ports.repository import IAuditLogRepository
from backend.infrastructure.database.mappers import audit_to_orm, orm_to_audit
from backend.infrastructure.database.models import AuditLogModel
from .base_sqlite import BaseSQLiteRepository


class SQLiteAuditLogRepository(BaseSQLiteRepository[AuditLog, AuditLogModel], IAuditLogRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AuditLogModel, audit_to_orm, orm_to_audit)

    async def list_by_actor(self, actor_id: str, limit: int = 50) -> list[AuditLog]:
        stmt = (
            select(AuditLogModel)
            .where(AuditLogModel.actor_id == actor_id)
            .order_by(AuditLogModel.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [orm_to_audit(m) for m in result.scalars().all()]

    async def list_by_resource(self, resource_type: str, resource_id: str) -> list[AuditLog]:
        stmt = (
            select(AuditLogModel)
            .where(
                AuditLogModel.resource_type == resource_type,
                AuditLogModel.resource_id == resource_id,
            )
            .order_by(AuditLogModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return [orm_to_audit(m) for m in result.scalars().all()]
