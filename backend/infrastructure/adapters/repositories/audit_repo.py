"""SQLite repository for AuditLogEntry entities.

Audit logs are append-only by convention: update() and delete()
are intentionally unsupported at the application layer.
"""
from __future__ import annotations

from typing import List

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.domain.models import AuditLogEntry
from backend.infrastructure.adapters.repositories.base_sqlite import BaseSQLiteRepository


class AuditLogRepository(BaseSQLiteRepository[AuditLogEntry]):
    model = AuditLogEntry

    async def find_by_actor(
        self, actor_id: str, session: AsyncSession, limit: int = 200
    ) -> List[AuditLogEntry]:
        result = await session.exec(
            select(AuditLogEntry)
            .where(AuditLogEntry.actor_id == actor_id)
            .order_by(AuditLogEntry.created_at.desc())  # type: ignore[arg-type]
            .limit(limit)
        )
        return list(result.all())

    async def find_by_action(
        self, action: str, session: AsyncSession, limit: int = 200
    ) -> List[AuditLogEntry]:
        result = await session.exec(
            select(AuditLogEntry)
            .where(AuditLogEntry.action == action)
            .order_by(AuditLogEntry.created_at.desc())  # type: ignore[arg-type]
            .limit(limit)
        )
        return list(result.all())

    async def find_by_resource(
        self, resource: str, session: AsyncSession, limit: int = 200
    ) -> List[AuditLogEntry]:
        result = await session.exec(
            select(AuditLogEntry)
            .where(AuditLogEntry.resource == resource)
            .order_by(AuditLogEntry.created_at.desc())  # type: ignore[arg-type]
            .limit(limit)
        )
        return list(result.all())
