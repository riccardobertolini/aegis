"""SQLite repository for Role and Permission entities."""
from __future__ import annotations

from typing import List, Optional

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.domain.models import Permission, Role
from backend.infrastructure.adapters.repositories.base_sqlite import BaseSQLiteRepository


class RoleRepository(BaseSQLiteRepository[Role]):
    """Concrete repository for Role."""

    model = Role

    async def find_by_name(
        self, name: str, session: AsyncSession
    ) -> Optional[Role]:
        result = await session.exec(select(Role).where(Role.name == name))
        return result.first()

    async def find_all_active(self, session: AsyncSession) -> List[Role]:
        result = await session.exec(select(Role).where(Role.is_active == True))  # noqa: E712
        return list(result.all())


class PermissionRepository(BaseSQLiteRepository[Permission]):
    """Concrete repository for Permission."""

    model = Permission

    async def find_by_role(
        self, role_id: str, session: AsyncSession
    ) -> List[Permission]:
        result = await session.exec(
            select(Permission).where(Permission.role_id == role_id)
        )
        return list(result.all())

    async def find_by_resource(
        self, resource: str, session: AsyncSession
    ) -> List[Permission]:
        result = await session.exec(
            select(Permission).where(Permission.resource == resource)
        )
        return list(result.all())
