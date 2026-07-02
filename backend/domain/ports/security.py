"""Port: Security Engine — extended for Phase 6."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class Permission(str, Enum):
    # Model management
    MODEL_READ = "model:read"
    MODEL_WRITE = "model:write"
    MODEL_DELETE = "model:delete"
    MODEL_INFER = "model:infer"
    MODEL_TRAIN = "model:train"
    # Document management
    DOCUMENT_READ = "document:read"
    DOCUMENT_WRITE = "document:write"
    DOCUMENT_DELETE = "document:delete"
    # User management
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    USER_DELETE = "user:delete"
    # Role management
    ROLE_READ = "role:read"
    ROLE_WRITE = "role:write"
    # Audit
    AUDIT_READ = "audit:read"
    # Knowledge
    KNOWLEDGE_READ = "knowledge:read"
    KNOWLEDGE_WRITE = "knowledge:write"
    # Plugin
    PLUGIN_MANAGE = "plugin:manage"
    # Administration
    ADMIN_FULL = "admin:full"
    # Backup
    BACKUP_CREATE = "backup:create"
    BACKUP_RESTORE = "backup:restore"


# Predefined role bundles
DEFAULT_ROLES: dict[str, list[Permission]] = {
    "superadmin": list(Permission),
    "admin": [
        Permission.MODEL_READ, Permission.MODEL_WRITE, Permission.MODEL_INFER, Permission.MODEL_TRAIN,
        Permission.DOCUMENT_READ, Permission.DOCUMENT_WRITE, Permission.DOCUMENT_DELETE,
        Permission.USER_READ, Permission.USER_WRITE,
        Permission.ROLE_READ, Permission.AUDIT_READ,
        Permission.KNOWLEDGE_READ, Permission.KNOWLEDGE_WRITE,
        Permission.PLUGIN_MANAGE, Permission.BACKUP_CREATE,
    ],
    "operator": [
        Permission.MODEL_READ, Permission.MODEL_INFER,
        Permission.DOCUMENT_READ, Permission.DOCUMENT_WRITE,
        Permission.KNOWLEDGE_READ, Permission.KNOWLEDGE_WRITE,
    ],
    "viewer": [
        Permission.MODEL_READ, Permission.MODEL_INFER,
        Permission.DOCUMENT_READ, Permission.KNOWLEDGE_READ,
    ],
}


@dataclass
class UserCredentials:
    username: str
    password: str


@dataclass
class AuthToken:
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime = field(default_factory=datetime.utcnow)
    session_id: Optional[str] = None


@dataclass
class UserPrincipal:
    user_id: str
    username: str
    roles: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)


@dataclass
class ModelIntegrityResult:
    model_id: str
    is_valid: bool
    stored_hash: str
    computed_hash: str
    algorithm: str = "sha256"
    checked_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AuditEntry:
    event_type: str
    actor_id: str
    actor_username: str
    resource: str
    action: str
    outcome: str  # "success" | "denied" | "error"
    details: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None


class ISecurityPort(ABC):
    """Contract for AuthN/AuthZ, RBAC, audit, encryption and integrity."""

    # --- Authentication ---
    @abstractmethod
    async def authenticate(self, credentials: UserCredentials) -> AuthToken: ...

    @abstractmethod
    async def verify_token(self, token: str) -> UserPrincipal: ...

    @abstractmethod
    async def revoke_session(self, session_id: str) -> None: ...

    @abstractmethod
    async def list_active_sessions(self, user_id: str) -> list[dict]: ...

    # --- Password ---
    @abstractmethod
    async def hash_password(self, password: str) -> str: ...

    @abstractmethod
    async def verify_password(self, password: str, hashed: str) -> bool: ...

    # --- RBAC ---
    @abstractmethod
    async def authorize(self, principal: UserPrincipal, resource: str, action: str) -> bool: ...

    @abstractmethod
    async def get_permissions_for_roles(self, roles: list[str]) -> list[Permission]: ...

    # --- Encryption ---
    @abstractmethod
    async def encrypt(self, plaintext: bytes) -> bytes: ...

    @abstractmethod
    async def decrypt(self, ciphertext: bytes) -> bytes: ...

    @abstractmethod
    async def rotate_key(self) -> str: ...

    # --- Model integrity ---
    @abstractmethod
    async def register_model_hash(self, model_id: str, model_path: str) -> str: ...

    @abstractmethod
    async def verify_model_integrity(self, model_id: str, model_path: str) -> ModelIntegrityResult: ...

    # --- Audit ---
    @abstractmethod
    async def log_audit(self, entry: AuditEntry) -> None: ...

    @abstractmethod
    async def query_audit(
        self,
        actor_id: Optional[str] = None,
        resource: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 100,
    ) -> list[AuditEntry]: ...

    # --- Backup ---
    @abstractmethod
    async def create_encrypted_backup(self, source_path: str, dest_path: str) -> str: ...

    @abstractmethod
    async def restore_encrypted_backup(self, backup_path: str, dest_path: str) -> None: ...
