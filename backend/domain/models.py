"""Domain models — SQLModel table definitions.

All models live here so Alembic env.py and test fixtures
can import a single module to register every table.

Naming convention:
- Table names are lowercase, singular (SQLModel default).
- FKs use string IDs (UUID serialised as str) for SQLite compatibility.
- Encrypted fields carry the suffix `_enc`.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlmodel import Field, SQLModel


def _now() -> datetime:
    return datetime.utcnow()


def _uuid() -> str:
    return str(uuid4())


# ---------------------------------------------------------------------------
# Role & Permission
# ---------------------------------------------------------------------------

class Role(SQLModel, table=True):
    id: str = Field(default_factory=_uuid, primary_key=True)
    name: str = Field(max_length=64, unique=True, index=True)
    description: Optional[str] = None
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


class Permission(SQLModel, table=True):
    id: str = Field(default_factory=_uuid, primary_key=True)
    role_id: str = Field(foreign_key="role.id", index=True)
    resource: str = Field(max_length=128)
    action: str = Field(max_length=32)
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

class User(SQLModel, table=True):
    id: str = Field(default_factory=_uuid, primary_key=True)
    username: str = Field(max_length=128, unique=True, index=True)
    email: Optional[str] = Field(default=None, max_length=256)
    hashed_password: str
    role_id: Optional[str] = Field(default=None, foreign_key="role.id")
    is_active: bool = Field(default=True)
    last_login: Optional[datetime] = None
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


# ---------------------------------------------------------------------------
# Assistant
# ---------------------------------------------------------------------------

class Assistant(SQLModel, table=True):
    id: str = Field(default_factory=_uuid, primary_key=True)
    name: str = Field(max_length=256)
    description: Optional[str] = None
    # AES-256-GCM encrypted fields
    system_prompt_enc: Optional[str] = None
    config_enc: Optional[str] = None
    is_active: bool = Field(default=True)
    owner_id: Optional[str] = Field(default=None, foreign_key="user.id")
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


# ---------------------------------------------------------------------------
# Knowledge Base & Category
# ---------------------------------------------------------------------------

class KnowledgeBase(SQLModel, table=True):
    id: str = Field(default_factory=_uuid, primary_key=True)
    name: str = Field(max_length=256, unique=True)
    description: Optional[str] = None
    assistant_id: Optional[str] = Field(default=None, foreign_key="assistant.id")
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


class Category(SQLModel, table=True):
    id: str = Field(default_factory=_uuid, primary_key=True)
    name: str = Field(max_length=256)
    knowledge_base_id: str = Field(foreign_key="knowledgebase.id", index=True)
    parent_id: Optional[str] = Field(default=None, foreign_key="category.id")
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


# ---------------------------------------------------------------------------
# Document
# ---------------------------------------------------------------------------

class Document(SQLModel, table=True):
    id: str = Field(default_factory=_uuid, primary_key=True)
    filename: str = Field(max_length=512)
    original_filename: str = Field(max_length=512)
    mime_type: Optional[str] = Field(default=None, max_length=128)
    size_bytes: Optional[int] = None
    sha256: Optional[str] = Field(default=None, max_length=64, index=True)
    storage_path: str = Field(max_length=1024)
    is_encrypted: bool = Field(default=False)
    knowledge_base_id: Optional[str] = Field(default=None, foreign_key="knowledgebase.id")
    category_id: Optional[str] = Field(default=None, foreign_key="category.id")
    uploader_id: Optional[str] = Field(default=None, foreign_key="user.id")
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


# ---------------------------------------------------------------------------
# Model (AI)
# ---------------------------------------------------------------------------

class AegisModel(SQLModel, table=True):
    id: str = Field(default_factory=_uuid, primary_key=True)
    name: str = Field(max_length=256)
    architecture: str = Field(max_length=64, default="mamba-ssm")
    storage_path: str = Field(max_length=1024)
    size_bytes: Optional[int] = None
    sha256: Optional[str] = Field(default=None, max_length=64)
    is_active: bool = Field(default=False)
    metadata_json: Optional[str] = None
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------

class Dataset(SQLModel, table=True):
    id: str = Field(default_factory=_uuid, primary_key=True)
    name: str = Field(max_length=256)
    storage_path: str = Field(max_length=1024)
    model_id: Optional[str] = Field(default=None, foreign_key="aegismodel.id")
    status: str = Field(default="pending", max_length=32)
    row_count: Optional[int] = None
    size_bytes: Optional[int] = None
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


# ---------------------------------------------------------------------------
# Memory
# ---------------------------------------------------------------------------

class MemoryChunk(SQLModel, table=True):
    id: str = Field(default_factory=_uuid, primary_key=True)
    assistant_id: str = Field(foreign_key="assistant.id", index=True)
    user_id: Optional[str] = Field(default=None, foreign_key="user.id")
    # Stored encrypted; plaintext never persisted
    content_enc: str
    embedding_path: Optional[str] = Field(default=None, max_length=1024)
    importance: float = Field(default=0.5)
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


# ---------------------------------------------------------------------------
# Version
# ---------------------------------------------------------------------------

class Version(SQLModel, table=True):
    id: str = Field(default_factory=_uuid, primary_key=True)
    entity_type: str = Field(max_length=64, index=True)
    entity_id: str = Field(index=True)
    version_number: int
    tag: Optional[str] = Field(default=None, max_length=64)
    # Full JSON snapshot of the entity at this version
    snapshot_json: str
    created_by: Optional[str] = None
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


# ---------------------------------------------------------------------------
# Workflow
# ---------------------------------------------------------------------------

class Workflow(SQLModel, table=True):
    id: str = Field(default_factory=_uuid, primary_key=True)
    name: str = Field(max_length=256)
    definition_json: str
    assistant_id: Optional[str] = Field(default=None, foreign_key="assistant.id")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


# ---------------------------------------------------------------------------
# Backup Record
# ---------------------------------------------------------------------------

class BackupRecord(SQLModel, table=True):
    id: str = Field(default_factory=_uuid, primary_key=True)
    filename: str = Field(max_length=512)
    storage_path: str = Field(max_length=1024)
    size_bytes: Optional[int] = None
    sha256: Optional[str] = Field(default=None, max_length=64)
    is_encrypted: bool = Field(default=True)
    backup_type: str = Field(default="full", max_length=32)
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


# ---------------------------------------------------------------------------
# Audit Log
# ---------------------------------------------------------------------------

class AuditLogEntry(SQLModel, table=True):
    id: str = Field(default_factory=_uuid, primary_key=True)
    actor_id: Optional[str] = Field(default=None, index=True)
    action: str = Field(max_length=128, index=True)
    resource: Optional[str] = Field(default=None, max_length=256)
    resource_id: Optional[str] = None
    detail_json: Optional[str] = None
    ip_address: Optional[str] = Field(default=None, max_length=64)
    created_at: datetime = Field(default_factory=_now, index=True)
    updated_at: datetime = Field(default_factory=_now)
