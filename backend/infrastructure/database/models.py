"""SQLModel ORM models — one table per domain entity."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional

from sqlmodel import Column, Field, JSON, SQLModel, String


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


# ---------------------------------------------------------------------------
# Users / Roles / Permissions
# ---------------------------------------------------------------------------

class PermissionModel(SQLModel, table=True):
    __tablename__ = "permissions"
    id: str = Field(primary_key=True)
    name: str = Field(index=True, unique=True)
    description: str = Field(default="")
    resource: str = Field(default="", index=True)
    action: str = Field(default="")
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class RoleModel(SQLModel, table=True):
    __tablename__ = "roles"
    id: str = Field(primary_key=True)
    name: str = Field(index=True, unique=True)
    description: str = Field(default="")
    permissions_json: str = Field(default="[]")  # JSON list of permission IDs
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)

    def get_permissions(self) -> list[str]:
        return json.loads(self.permissions_json)

    def set_permissions(self, ids: list[str]) -> None:
        self.permissions_json = json.dumps(ids)


class UserModel(SQLModel, table=True):
    __tablename__ = "users"
    id: str = Field(primary_key=True)
    username: str = Field(index=True, unique=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str = Field(default="")
    role_ids_json: str = Field(default="[]")  # JSON list
    is_active: bool = Field(default=True)
    is_superadmin: bool = Field(default=False)
    last_login_at: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


# ---------------------------------------------------------------------------
# Assistant
# ---------------------------------------------------------------------------

class AssistantModel(SQLModel, table=True):
    __tablename__ = "assistants"
    id: str = Field(primary_key=True)
    name: str = Field(index=True)
    description: str = Field(default="")
    owner_id: str = Field(index=True)
    config_json: str = Field(default="{}")  # JSON AssistantConfig
    is_active: bool = Field(default=True)
    version: int = Field(default=1)
    knowledge_base_ids_json: str = Field(default="[]")
    plugin_ids_json: str = Field(default="[]")
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


# ---------------------------------------------------------------------------
# Documents / Categories / KnowledgeBases
# ---------------------------------------------------------------------------

class CategoryModel(SQLModel, table=True):
    __tablename__ = "categories"
    id: str = Field(primary_key=True)
    name: str = Field(index=True)
    description: str = Field(default="")
    parent_id: Optional[str] = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class DocumentModel(SQLModel, table=True):
    __tablename__ = "documents"
    id: str = Field(primary_key=True)
    filename: str = Field(default="")
    original_filename: str = Field(default="")
    mime_type: str = Field(default="")
    size_bytes: int = Field(default=0)
    checksum_sha256: str = Field(default="", index=True)
    storage_path: str = Field(default="")
    status: str = Field(default="pending", index=True)
    owner_id: str = Field(index=True)
    category_ids_json: str = Field(default="[]")
    knowledge_base_ids_json: str = Field(default="[]")
    metadata_json: str = Field(default="{}")
    is_encrypted: bool = Field(default=False)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class KnowledgeBaseModel(SQLModel, table=True):
    __tablename__ = "knowledge_bases"
    id: str = Field(primary_key=True)
    name: str = Field(index=True, unique=True)
    description: str = Field(default="")
    owner_id: str = Field(index=True)
    category_ids_json: str = Field(default="[]")
    is_active: bool = Field(default=True)
    chroma_collection_name: str = Field(default="")
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


# ---------------------------------------------------------------------------
# Memory
# ---------------------------------------------------------------------------

class MemoryEntryModel(SQLModel, table=True):
    __tablename__ = "memory_entries"
    id: str = Field(primary_key=True)
    session_id: str = Field(index=True)
    assistant_id: str = Field(index=True)
    user_id: str = Field(index=True)
    role: str = Field(default="user")
    content: str = Field(default="")  # may be encrypted ciphertext
    embedding_id: Optional[str] = Field(default=None)
    metadata_json: str = Field(default="{}")
    is_encrypted: bool = Field(default=False)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


# ---------------------------------------------------------------------------
# Models / Datasets
# ---------------------------------------------------------------------------

class ModelRecordModel(SQLModel, table=True):
    __tablename__ = "model_records"
    id: str = Field(primary_key=True)
    name: str = Field(index=True, unique=True)
    model_type: str = Field(default="ssm_mamba")
    status: str = Field(default="unavailable", index=True)
    storage_path: str = Field(default="")
    checksum_sha256: str = Field(default="")
    size_bytes: int = Field(default=0)
    architecture: str = Field(default="")
    context_length: int = Field(default=2048)
    metadata_json: str = Field(default="{}")
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class DatasetModel(SQLModel, table=True):
    __tablename__ = "datasets"
    id: str = Field(primary_key=True)
    name: str = Field(index=True)
    description: str = Field(default="")
    storage_path: str = Field(default="")
    format: str = Field(default="jsonl")
    size_bytes: int = Field(default=0)
    checksum_sha256: str = Field(default="")
    row_count: int = Field(default=0)
    owner_id: str = Field(index=True)
    metadata_json: str = Field(default="{}")
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


# ---------------------------------------------------------------------------
# Workflow / Rule
# ---------------------------------------------------------------------------

class WorkflowModel(SQLModel, table=True):
    __tablename__ = "workflows"
    id: str = Field(primary_key=True)
    name: str = Field(index=True)
    description: str = Field(default="")
    owner_id: str = Field(index=True)
    status: str = Field(default="draft", index=True)
    steps_json: str = Field(default="[]")
    metadata_json: str = Field(default="{}")
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class RuleModel(SQLModel, table=True):
    __tablename__ = "rules"
    id: str = Field(primary_key=True)
    name: str = Field(index=True)
    description: str = Field(default="")
    resource: str = Field(index=True)
    condition_json: str = Field(default="{}")
    action: str = Field(default="")
    priority: int = Field(default=0, index=True)
    is_active: bool = Field(default=True, index=True)
    owner_id: str = Field(index=True)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


# ---------------------------------------------------------------------------
# Audit Log
# ---------------------------------------------------------------------------

class AuditLogModel(SQLModel, table=True):
    __tablename__ = "audit_logs"
    id: str = Field(primary_key=True)
    actor_id: str = Field(index=True)
    actor_username: str = Field(default="")
    action: str = Field(index=True)
    resource_type: str = Field(index=True)
    resource_id: str = Field(index=True)
    outcome: str = Field(default="ok")
    ip_address: Optional[str] = Field(default=None)
    details_json: str = Field(default="{}")
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


# ---------------------------------------------------------------------------
# Backup
# ---------------------------------------------------------------------------

class BackupModel(SQLModel, table=True):
    __tablename__ = "backups"
    id: str = Field(primary_key=True)
    label: str = Field(default="")
    storage_path: str = Field(default="")
    checksum_sha256: str = Field(default="")
    size_bytes: int = Field(default=0)
    status: str = Field(default="pending", index=True)
    includes_json: str = Field(default="[]")
    initiated_by: str = Field(default="")
    error_message: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


# ---------------------------------------------------------------------------
# Config store (key-value, optionally encrypted)
# ---------------------------------------------------------------------------

class ConfigEntryModel(SQLModel, table=True):
    __tablename__ = "config_entries"
    id: str = Field(primary_key=True)
    scope: str = Field(index=True)  # "global" or assistant_id
    key: str = Field(index=True)
    value_json: str = Field(default="null")  # JSON-encoded value
    is_encrypted: bool = Field(default=False)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
