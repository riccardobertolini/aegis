"""Dependency Injection container — wires all infrastructure adapters.

This module is the single place where concrete implementations are
instantiated and bound to their Port interfaces.  Application-layer
use-cases receive the Port (interface), never the concrete class.

No cloud service, remote DB, or external HTTP call is ever wired here.
"""
from __future__ import annotations

from functools import lru_cache
from typing import AsyncGenerator

from sqlmodel.ext.asyncio.session import AsyncSession

from backend.infrastructure.adapters.backup_manager import BackupManager
from backend.infrastructure.adapters.config_manager import ConfigManager
from backend.infrastructure.adapters.encryption import EncryptionService
from backend.infrastructure.adapters.repositories import (
    AssistantRepository,
    AuditLogRepository,
    BackupRepository,
    CategoryRepository,
    DatasetRepository,
    DocumentRepository,
    KnowledgeBaseRepository,
    MemoryRepository,
    ModelRepository,
    PermissionRepository,
    RoleRepository,
    UserRepository,
    VersionRepository,
    WorkflowRepository,
)
from backend.infrastructure.adapters.storage import StorageManager
from backend.infrastructure.db.engine import get_async_session_factory


@lru_cache(maxsize=1)
def get_encryption_service() -> EncryptionService:
    """Singleton encryption service (key derived from local keyfile)."""
    return EncryptionService()


@lru_cache(maxsize=1)
def get_config_manager() -> ConfigManager:
    return ConfigManager(encryption=get_encryption_service())


@lru_cache(maxsize=1)
def get_storage_manager() -> StorageManager:
    return StorageManager(encryption=get_encryption_service())


@lru_cache(maxsize=1)
def get_backup_manager() -> BackupManager:
    return BackupManager(
        storage=get_storage_manager(),
        encryption=get_encryption_service(),
    )


# ------------------------------------------------------------------
# FastAPI dependency factories — one per repository
# ------------------------------------------------------------------

async def _session() -> AsyncGenerator[AsyncSession, None]:
    factory = get_async_session_factory()
    async with factory() as s:
        yield s


def get_assistant_repo() -> AssistantRepository:
    return AssistantRepository()


def get_user_repo() -> UserRepository:
    return UserRepository()


def get_role_repo() -> RoleRepository:
    return RoleRepository()


def get_permission_repo() -> PermissionRepository:
    return PermissionRepository()


def get_document_repo() -> DocumentRepository:
    return DocumentRepository()


def get_knowledge_repo() -> KnowledgeBaseRepository:
    return KnowledgeBaseRepository()


def get_category_repo() -> CategoryRepository:
    return CategoryRepository()


def get_memory_repo() -> MemoryRepository:
    return MemoryRepository()


def get_model_repo() -> ModelRepository:
    return ModelRepository()


def get_dataset_repo() -> DatasetRepository:
    return DatasetRepository()


def get_workflow_repo() -> WorkflowRepository:
    return WorkflowRepository()


def get_version_repo() -> VersionRepository:
    return VersionRepository()


def get_audit_repo() -> AuditLogRepository:
    return AuditLogRepository()


def get_backup_repo() -> BackupRepository:
    return BackupRepository()
