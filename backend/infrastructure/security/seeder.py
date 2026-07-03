"""Bootstrap: create default roles and superadmin user if DB is empty."""
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from backend.domain.ports.security import DEFAULT_ROLES
from backend.infrastructure.security.models import RoleModel, RolePermissionLink, UserModel
from backend.infrastructure.security.password import hash_password

log = logging.getLogger(__name__)


async def seed_roles(session: AsyncSession) -> None:
    """Create system roles from DEFAULT_ROLES if they don't exist yet."""
    for role_name, perms in DEFAULT_ROLES.items():
        result = await session.execute(
            select(RoleModel).where(RoleModel.name == role_name)
        )
        if result.scalars().first() is None:
            role = RoleModel(name=role_name, is_system=True)
            session.add(role)
            await session.flush()
            for perm in perms:
                session.add(RolePermissionLink(role_id=role.id, permission=perm.value))
    await session.commit()
    log.info("Security roles seeded")


async def seed_superadmin(
    session: AsyncSession,
    username: str = "admin",
    password: str = "ChangeMe123!",
) -> None:
    """Create a default superadmin user if no users exist."""
    result = await session.execute(select(UserModel))
    if result.scalars().first() is not None:
        return  # Users already exist — skip
    result = await session.execute(
        select(RoleModel).where(RoleModel.name == "superadmin")
    )
    role = result.scalars().first()
    user = UserModel(
        username=username,
        hashed_password=hash_password(password),
    )
    if role:
        user.roles = [role]
    session.add(user)
    await session.commit()
    log.warning(
        "⚠️  Default superadmin created — change password immediately! "
        "Username: %s", username
    )
