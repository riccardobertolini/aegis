"""SQLite repository for Version entities (assistants, models, documents)."""
from __future__ import annotations

from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.domain.models import Version
from backend.infrastructure.adapters.repositories.base_sqlite import BaseSQLiteRepository


class VersionRepository(BaseSQLiteRepository[Version]):
    """Concrete repository for Version."""

    model = Version

    async def find_by_entity(
        self,
        entity_type: str,
        entity_id: UUID,
        session: AsyncSession,
    ) -> list[Version]:
        result = await session.exec(
            select(Version)
            .where(Version.entity_type == entity_type)
            .where(Version.entity_id == entity_id)
            .order_by(Version.version_number.desc())  # type: ignore[arg-type]
        )
        return list(result.all())

    async def find_latest(
        self,
        entity_type: str,
        entity_id: UUID,
        session: AsyncSession,
    ) -> Version | None:
        result = await session.exec(
            select(Version)
            .where(Version.entity_type == entity_type)
            .where(Version.entity_id == entity_id)
            .order_by(Version.version_number.desc())  # type: ignore[arg-type]
            .limit(1)
        )
        return result.first()

    async def find_by_tag(
        self,
        entity_type: str,
        entity_id: UUID,
        tag: str,
        session: AsyncSession,
    ) -> Version | None:
        result = await session.exec(
            select(Version)
            .where(Version.entity_type == entity_type)
            .where(Version.entity_id == entity_id)
            .where(Version.tag == tag)
        )
        return result.first()
