"""Concrete SecurityService: implements ISecurityPort.

Dependencies injected at construction time (DI-friendly):
  - AsyncSession  (SQLite via aiosqlite)
  - LocalKeyStore (local AES-256-GCM keystore)
  - BackupService
  - RBACEnforcer
"""
import hashlib
import json
import secrets
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from backend.domain.ports.security import (
    AuditEntry,
    AuthToken,
    ISecurityPort,
    ModelIntegrityResult,
    Permission,
    UserCredentials,
    UserPrincipal,
)
from backend.shared.exceptions import AuthenticationError, AuthorizationError
from backend.infrastructure.security.audit import AuditWriter, AuditReader
from backend.infrastructure.security.backup import BackupService
from backend.infrastructure.security.encryption import LocalKeyStore
from backend.infrastructure.security.integrity import ModelIntegrityService
from backend.infrastructure.security.models import (
    SessionModel,
    UserModel,
    RoleModel,
    RolePermissionLink,
)
from backend.infrastructure.security.password import hash_password, verify_password
from backend.infrastructure.security.rbac import RBACEnforcer
from backend.infrastructure.security.token import (
    create_access_token,
    decode_access_token,
    hash_token,
)

_MAX_FAILED = 5  # Lock account after N consecutive failures
_SESSION_EXPIRY_MINUTES = 60


class SecurityService(ISecurityPort):
    def __init__(
        self,
        session: AsyncSession,
        keystore: LocalKeyStore,
        backup_passphrase: str,
        rbac: Optional[RBACEnforcer] = None,
    ) -> None:
        self._session = session
        self._keystore = keystore
        self._backup = BackupService(backup_passphrase)
        self._rbac = rbac or RBACEnforcer()
        _audit_key = hashlib.sha256(b"audit:" + keystore._master_key).digest()  # type: ignore[arg-type]
        self._audit_writer = AuditWriter(session, _audit_key)
        self._audit_reader = AuditReader(session, _audit_key)
        self._integrity = ModelIntegrityService(session)

    # ─── Authentication ────────────────────────────────────────────────────────

    async def authenticate(self, credentials: UserCredentials) -> AuthToken:
        result = await self._session.execute(
            select(UserModel).where(UserModel.username == credentials.username)
        )
        user = result.scalars().first()
        await self.log_audit(AuditEntry(
            event_type="auth.login",
            actor_id=user.id if user else "unknown",
            actor_username=credentials.username,
            resource="session",
            action="authenticate",
            outcome="success" if (user and not user.is_locked) else "denied",
        ))
        if not user or user.is_locked:
            raise AuthenticationError("Invalid credentials or account locked")
        if not verify_password(credentials.password, user.hashed_password):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= _MAX_FAILED:
                user.is_locked = True
            self._session.add(user)
            await self._session.commit()
            raise AuthenticationError("Invalid credentials")

        user.failed_login_attempts = 0
        user.last_login_at = datetime.utcnow()
        self._session.add(user)

        roles = [r.name for r in user.roles]
        perms = [p.value for p in self._rbac.resolve(roles)]
        session_id = secrets.token_hex(16)
        token, expires_at = create_access_token(
            user.id, user.username, roles, perms, session_id, _SESSION_EXPIRY_MINUTES
        )
        self._session.add(SessionModel(
            id=session_id,
            user_id=user.id,
            token_hash=hash_token(token),
            expires_at=expires_at,
        ))
        await self._session.commit()
        return AuthToken(access_token=token, expires_at=expires_at, session_id=session_id)

    async def verify_token(self, token: str) -> UserPrincipal:
        payload = decode_access_token(token)  # raises AuthenticationError if invalid
        session_id = payload.get("session_id")
        session = await self._session.get(SessionModel, session_id)
        if not session or not session.is_valid:
            raise AuthenticationError("Session revoked or expired")
        return UserPrincipal(
            user_id=payload["sub"],
            username=payload["username"],
            roles=payload["roles"],
            permissions=payload["permissions"],
        )

    async def revoke_session(self, session_id: str) -> None:
        session = await self._session.get(SessionModel, session_id)
        if session:
            session.revoked_at = datetime.utcnow()
            self._session.add(session)
            await self._session.commit()

    async def list_active_sessions(self, user_id: str) -> list[dict]:
        result = await self._session.execute(
            select(SessionModel)
            .where(SessionModel.user_id == user_id)
            .where(SessionModel.revoked_at.is_(None))  # type: ignore[attr-defined]
            .where(SessionModel.expires_at > datetime.utcnow())
        )
        return [
            {"session_id": s.id, "issued_at": s.issued_at.isoformat(),
             "expires_at": s.expires_at.isoformat(), "ip_address": s.ip_address}
            for s in result.scalars().all()
        ]

    # ─── Password ─────────────────────────────────────────────────────────────

    async def hash_password(self, password: str) -> str:
        return hash_password(password)

    async def verify_password(self, password: str, hashed: str) -> bool:
        return verify_password(password, hashed)

    # ─── RBAC ─────────────────────────────────────────────────────────────────

    async def authorize(
        self, principal: UserPrincipal, resource: str, action: str
    ) -> bool:
        perm = self._rbac.parse_resource_action(resource, action)
        if perm is None:
            return False
        return self._rbac.may(principal.roles, perm)

    async def get_permissions_for_roles(self, roles: list[str]) -> list[Permission]:
        return list(self._rbac.resolve(roles))

    # ─── Encryption ───────────────────────────────────────────────────────────

    async def encrypt(self, plaintext: bytes) -> bytes:
        return self._keystore.encrypt(plaintext)

    async def decrypt(self, ciphertext: bytes) -> bytes:
        return self._keystore.decrypt(ciphertext)

    async def rotate_key(self) -> str:
        return self._keystore.rotate()

    # ─── Model integrity ──────────────────────────────────────────────────────

    async def register_model_hash(self, model_id: str, model_path: str) -> str:
        return await self._integrity.register(model_id, model_path)

    async def verify_model_integrity(
        self, model_id: str, model_path: str
    ) -> ModelIntegrityResult:
        return await self._integrity.verify(model_id, model_path)

    # ─── Audit ────────────────────────────────────────────────────────────────

    async def log_audit(self, entry: AuditEntry) -> None:
        await self._audit_writer.append(entry)

    async def query_audit(
        self,
        actor_id: Optional[str] = None,
        resource: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 100,
    ) -> list[AuditEntry]:
        return await self._audit_reader.query(actor_id, resource, since, until, limit)

    # ─── Backup ───────────────────────────────────────────────────────────────

    async def create_encrypted_backup(self, source_path: str, dest_path: str) -> str:
        return self._backup.create(source_path, dest_path)

    async def restore_encrypted_backup(self, backup_path: str, dest_path: str) -> None:
        self._backup.restore(backup_path, dest_path)
