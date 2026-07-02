"""Concrete SQLite User repository."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.entities.user import Permission, Role, User
from backend.domain.ports.repository import IAssistantRepository, IPermissionRepository, IRoleRepository, IUserRepository
from backend.infrastructure.database.mappers import (
    orm_to_permission, orm_to_role, orm_to_user,
    permission_to_orm, role_to_orm, user_to_orm,
)
from backend.infrastructure.database.models import PermissionModel, RoleModel, UserModel
from .base_sqlite import BaseSQLiteRepository


class SQLiteUserRepository(BaseSQLiteRepository[User, UserModel], IUserRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, UserModel, user_to_orm, orm_to_user)

    async def get_by_username(self, username: str) -> User | None:
        stmt = select(UserModel).where(UserModel.username == username)
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        return orm_to_user(m) if m else None

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        return orm_to_user(m) if m else None


class SQLiteRoleRepository(BaseSQLiteRepository[Role, RoleModel], IRoleRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, RoleModel, role_to_orm, orm_to_role)

    async def get_by_name(self, name: str) -> Role | None:
        stmt = select(RoleModel).where(RoleModel.name == name)
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        return orm_to_role(m) if m else None


class SQLitePermissionRepository(BaseSQLiteRepository[Permission, PermissionModel], IPermissionRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, PermissionModel, permission_to_orm, orm_to_permission)

    async def list_by_resource(self, resource: str) -> list[Permission]:
        stmt = select(PermissionModel).where(PermissionModel.resource == resource)
        result = await self._session.execute(stmt)
        return [orm_to_permission(m) for m in result.scalars().all()]
