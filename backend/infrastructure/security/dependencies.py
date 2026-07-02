"""FastAPI dependency injection helpers for the Security Engine."""
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from backend.domain.ports.security import ISecurityPort, UserPrincipal
from backend.shared.config import get_settings
from backend.shared.exceptions import AuthenticationError, AuthorizationError


@lru_cache(maxsize=1)
def _get_security_service() -> ISecurityPort:  # type: ignore[return]
    """Returns the singleton SecurityService.  Replace at runtime with DI container."""
    # Import here to avoid circular imports at module load time.
    from backend.infrastructure.security.encryption import LocalKeyStore
    from backend.infrastructure.security.service import SecurityService
    from backend.infrastructure.db import get_sync_session  # provided by Phase 2

    settings = get_settings()
    keystore = LocalKeyStore(
        keystore_path=settings.security_keystore_path,  # type: ignore[attr-defined]
        passphrase=settings.security_keystore_passphrase,  # type: ignore[attr-defined]
    )
    # NOTE: For async usage a proper async-aware session factory should be used.
    # This singleton is suitable for startup initialisation and CLI tooling.
    return None  # Replaced at app startup via DI container


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    security: ISecurityPort = Depends(_get_security_service),
) -> UserPrincipal:
    """FastAPI dependency: parse Bearer token, return UserPrincipal."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    token = authorization.removeprefix("Bearer ")
    try:
        return await security.verify_token(token)
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


def require_permission(permission: str):
    """Factory: returns a FastAPI dependency that enforces a single permission."""
    async def _check(
        principal: UserPrincipal = Depends(get_current_user),
    ) -> UserPrincipal:
        if permission not in principal.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission}",
            )
        return principal
    return _check
