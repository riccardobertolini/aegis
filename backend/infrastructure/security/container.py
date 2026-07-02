"""Dependency Injection container for the Security Engine.

Call `build_security_container(session, settings)` at app startup.
Store the result on `app.state.security` and override the FastAPI
dependency with `app.dependency_overrides`.

Example (in main.py):

    @app.on_event("startup")
    async def _startup():
        async with get_async_session() as session:
            container = await build_security_container(session)
        app.state.security = container.service
        app.dependency_overrides[_placeholder_dep] = lambda: container.service
"""
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession

from backend.shared.config import Settings, get_settings
from backend.infrastructure.security.encryption import LocalKeyStore
from backend.infrastructure.security.rbac import RBACEnforcer
from backend.infrastructure.security.service import SecurityService
from backend.infrastructure.security.seeder import seed_roles, seed_superadmin


@dataclass
class SecurityContainer:
    keystore: LocalKeyStore
    enforcer: RBACEnforcer
    service: SecurityService


async def build_security_container(
    session: AsyncSession,
    settings: Settings | None = None,
) -> SecurityContainer:
    """Wire and return all security infrastructure components."""
    cfg = settings or get_settings()

    keystore = LocalKeyStore(
        keystore_path=cfg.security_keystore_path,
        passphrase=cfg.security_keystore_passphrase,
    )
    enforcer = RBACEnforcer()
    service = SecurityService(
        session=session,
        keystore=keystore,
        backup_passphrase=cfg.security_backup_passphrase,
        rbac=enforcer,
    )

    # Bootstrap DB with default roles and superadmin on first run
    await seed_roles(session)
    await seed_superadmin(session)

    return SecurityContainer(
        keystore=keystore,
        enforcer=enforcer,
        service=service,
    )
