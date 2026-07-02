"""SQLite repository for User entities.

Maps between SQLiteUserRepository (name used by di.py / Fase 6) and
the ORM model UserModel in database/models.py.
"""
from __future__ import annotations

from typing import List, Optional

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.infrastructure.adapters.repositories.base_sqlite import BaseSQLiteRepository
from backend.infrastructure.database.models import UserModel, RoleModel, PermissionModel


class SQLiteUserRepository(BaseSQLiteRepository[UserModel]):
    model = UserModel

    async def find_by_username(self, username: str) -> Optional[UserModel]:
        result = await self._session.exec(
            select(UserModel).where(UserModel.username == username)
        )
        return result.first()

    async def find_by_email(self, email: str) -> Optional[UserModel]:
        result = await self._session.exec(
            select(UserModel).where(UserModel.email == email)
        )
        return result.first()

    async def find_active(self) -> List[UserModel]:
        result = await self._session.exec(
            select(UserModel).where(UserModel.is_active == True)  # noqa: E712
        )
        return list(result.all())

    async def find_superadmins(self) -> List[UserModel]:
        result = await self._session.exec(
            select(UserModel).where(UserModel.is_superadmin == True)  # noqa: E712
        )
        return list(result.all())


# Alias: legacy callers used UserRepository
UserRepository = SQLiteUserRepository


class SQLiteRoleRepository(BaseSQLiteRepository[RoleModel]):
    model = RoleModel

    async def find_by_name(self, name: str) -> Optional[RoleModel]:
        result = await self._session.exec(
            select(RoleModel).where(RoleModel.name == name)
        )
        return result.first()

    async def find_many_by_ids(self, ids: list[str]) -> List[RoleModel]:
        result = await self._session.exec(
            select(RoleModel).where(RoleModel.id.in_(ids))  # type: ignore[attr-defined]
        )
        return list(result.all())


RoleRepository = SQLiteRoleRepository


class SQLitePermissionRepository(BaseSQLiteRepository[PermissionModel]):
    model = PermissionModel

    async def find_by_name(self, name: str) -> Optional[PermissionModel]:
        result = await self._session.exec(
            select(PermissionModel).where(PermissionModel.name == name)
        )
        return result.first()

    async def find_by_resource(self, resource: str) -> List[PermissionModel]:
        result = await self._session.exec(
            select(PermissionModel).where(PermissionModel.resource == resource)
        )
        return list(result.all())


PermissionRepository = SQLitePermissionRepository
