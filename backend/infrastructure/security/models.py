"""SQLModel DB models for RBAC, sessions, audit log, encryption keys."""
from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel, Relationship
import uuid


def _uuid() -> str:
    return str(uuid.uuid4())


# ─── Users & Roles ─────────────────────────────────────────────────────────────

class UserRoleLink(SQLModel, table=True):
    """Many-to-many: users ↔ roles."""
    __tablename__ = "user_role_links"
    user_id: Optional[str] = Field(default=None, foreign_key="users.id", primary_key=True)
    role_id: Optional[str] = Field(default=None, foreign_key="roles.id", primary_key=True)


class RolePermissionLink(SQLModel, table=True):
    """Many-to-many: roles ↔ permissions."""
    __tablename__ = "role_permission_links"
    role_id: Optional[str] = Field(default=None, foreign_key="roles.id", primary_key=True)
    permission: str = Field(primary_key=True)  # Permission enum value


class UserModel(SQLModel, table=True):
    __tablename__ = "users"
    id: str = Field(default_factory=_uuid, primary_key=True)
    username: str = Field(index=True, unique=True, max_length=128)
    hashed_password: str
    is_active: bool = Field(default=True)
    is_locked: bool = Field(default=False)
    failed_login_attempts: int = Field(default=0)
    last_login_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    roles: list["RoleModel"] = Relationship(link_model=UserRoleLink)
    sessions: list["SessionModel"] = Relationship(back_populates="user")


class RoleModel(SQLModel, table=True):
    __tablename__ = "roles"
    id: str = Field(default_factory=_uuid, primary_key=True)
    name: str = Field(index=True, unique=True, max_length=64)
    description: str = Field(default="", max_length=256)
    is_system: bool = Field(default=False)  # System roles cannot be deleted
    created_at: datetime = Field(default_factory=datetime.utcnow)

    users: list[UserModel] = Relationship(link_model=UserRoleLink)
    permissions: list[RolePermissionLink] = Relationship()


# ─── Sessions ──────────────────────────────────────────────────────────────────

class SessionModel(SQLModel, table=True):
    __tablename__ = "sessions"
    id: str = Field(default_factory=_uuid, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    token_hash: str = Field(index=True)  # SHA-256 of the raw JWT
    issued_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    revoked_at: Optional[datetime] = None
    ip_address: Optional[str] = Field(default=None, max_length=45)
    user_agent: Optional[str] = Field(default=None, max_length=256)

    user: Optional[UserModel] = Relationship(back_populates="sessions")

    @property
    def is_valid(self) -> bool:
        return self.revoked_at is None and self.expires_at > datetime.utcnow()


# ─── Audit log (append-only) ───────────────────────────────────────────────────

class AuditLogModel(SQLModel, table=True):
    """Immutable audit log.  Never update or delete rows."""
    __tablename__ = "audit_logs"
    id: str = Field(default_factory=_uuid, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
    event_type: str = Field(max_length=64, index=True)
    actor_id: str = Field(max_length=128, index=True)
    actor_username: str = Field(max_length=128)
    resource: str = Field(max_length=256)
    action: str = Field(max_length=64)
    outcome: str = Field(max_length=16)  # success | denied | error
    details_json: str = Field(default="{}")  # JSON-encoded dict
    ip_address: Optional[str] = Field(default=None, max_length=45)
    row_hmac: Optional[str] = Field(default=None)  # HMAC-SHA256 chained integrity


# ─── Encryption key registry ───────────────────────────────────────────────────

class EncryptionKeyModel(SQLModel, table=True):
    """Tracks active & retired encryption key versions."""
    __tablename__ = "encryption_keys"
    id: str = Field(default_factory=_uuid, primary_key=True)
    key_id: str = Field(index=True, unique=True, max_length=64)
    algorithm: str = Field(default="AES-256-GCM", max_length=32)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    retired_at: Optional[datetime] = None
    is_active: bool = Field(default=True)
    # The raw key material is NEVER stored in the DB.
    # It is stored only in the local keystore file, encrypted at rest.


# ─── Model integrity registry ──────────────────────────────────────────────────

class ModelHashModel(SQLModel, table=True):
    """Registered hash for each model file."""
    __tablename__ = "model_hashes"
    id: str = Field(default_factory=_uuid, primary_key=True)
    model_id: str = Field(index=True, unique=True, max_length=256)
    algorithm: str = Field(default="sha256", max_length=16)
    hash_value: str = Field(max_length=128)
    registered_at: datetime = Field(default_factory=datetime.utcnow)
    last_verified_at: Optional[datetime] = None
    last_verified_ok: Optional[bool] = None
