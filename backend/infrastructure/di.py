"""Dependency injection wiring for persistence layer.

Provides factory functions to build all concrete adapters,
consistently wired to the same SQLite session and encryption key.
FastAPI routers depend on these via Depends().
"""
from __future__ import annotations

from collections.abc import AsyncGenerator
from functools import lru_cache
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from backend.infrastructure.adapters.backup_manager import LocalBackupManager
from backend.infrastructure.adapters.config_manager import SQLiteConfigManager
from backend.infrastructure.adapters.encryption import LocalEncryptionAdapter
from backend.infrastructure.adapters.repositories.assistant_repo import SQLiteAssistantRepository
from backend.infrastructure.adapters.repositories.audit_repo import SQLiteAuditLogRepository
from backend.infrastructure.adapters.repositories.backup_repo import SQLiteBackupRepository
from backend.infrastructure.adapters.repositories.document_repo import (
    SQLiteCategoryRepository,
    SQLiteDocumentRepository,
    SQLiteKnowledgeBaseRepository,
)
from backend.infrastructure.adapters.repositories.memory_repo import SQLiteMemoryEntryRepository
from backend.infrastructure.adapters.repositories.model_repo import (
    SQLiteDatasetRepository,
    SQLiteModelRecordRepository,
)
from backend.infrastructure.adapters.repositories.user_repo import (
    SQLitePermissionRepository,
    SQLiteRoleRepository,
    SQLiteUserRepository,
)
from backend.infrastructure.adapters.repositories.workflow_repo import (
    SQLiteRuleRepository,
    SQLiteWorkflowRepository,
)
from backend.infrastructure.adapters.storage import LocalStorageAdapter
from backend.infrastructure.database.engine import get_session
from backend.shared.config import get_settings


@lru_cache(maxsize=1)
def get_encryption() -> LocalEncryptionAdapter:
    settings = get_settings()
    return LocalEncryptionAdapter(keys_dir=Path(settings.data_dir) / "keys")


@lru_cache(maxsize=1)
def get_document_storage() -> LocalStorageAdapter:
    settings = get_settings()
    return LocalStorageAdapter(
        base_dir=Path(settings.data_dir) / "documents",
        encryption=get_encryption(),
    )


@lru_cache(maxsize=1)
def get_model_storage() -> LocalStorageAdapter:
    settings = get_settings()
    return LocalStorageAdapter(
        base_dir=Path(settings.data_dir) / "models",
        encryption=None,  # models stored as-is; verify by checksum
    )


# --- Session-scoped factory functions (used as FastAPI dependencies) ---

async def session_dep() -> AsyncGenerator[AsyncSession, None]:
    async for s in get_session():
        yield s


def user_repo(session: AsyncSession) -> SQLiteUserRepository:
    return SQLiteUserRepository(session)

def role_repo(session: AsyncSession) -> SQLiteRoleRepository:
    return SQLiteRoleRepository(session)

def permission_repo(session: AsyncSession) -> SQLitePermissionRepository:
    return SQLitePermissionRepository(session)

def assistant_repo(session: AsyncSession) -> SQLiteAssistantRepository:
    return SQLiteAssistantRepository(session)

def document_repo(session: AsyncSession) -> SQLiteDocumentRepository:
    return SQLiteDocumentRepository(session)

def category_repo(session: AsyncSession) -> SQLiteCategoryRepository:
    return SQLiteCategoryRepository(session)

def kb_repo(session: AsyncSession) -> SQLiteKnowledgeBaseRepository:
    return SQLiteKnowledgeBaseRepository(session)

def memory_repo(session: AsyncSession) -> SQLiteMemoryEntryRepository:
    return SQLiteMemoryEntryRepository(session)

def model_record_repo(session: AsyncSession) -> SQLiteModelRecordRepository:
    return SQLiteModelRecordRepository(session)

def dataset_repo(session: AsyncSession) -> SQLiteDatasetRepository:
    return SQLiteDatasetRepository(session)

def workflow_repo_dep(session: AsyncSession) -> SQLiteWorkflowRepository:
    return SQLiteWorkflowRepository(session)

def rule_repo(session: AsyncSession) -> SQLiteRuleRepository:
    return SQLiteRuleRepository(session)

def audit_repo(session: AsyncSession) -> SQLiteAuditLogRepository:
    return SQLiteAuditLogRepository(session)

def backup_repo_dep(session: AsyncSession) -> SQLiteBackupRepository:
    return SQLiteBackupRepository(session)

def config_manager_dep(session: AsyncSession) -> SQLiteConfigManager:
    return SQLiteConfigManager(session, encryption=get_encryption())

def backup_manager_dep(session: AsyncSession) -> LocalBackupManager:
    settings = get_settings()
    return LocalBackupManager(
        backup_dir=Path(settings.data_dir) / "backups",
        data_dir=Path(settings.data_dir),
        encryption=get_encryption(),
        backup_repo=backup_repo_dep(session),
    )
