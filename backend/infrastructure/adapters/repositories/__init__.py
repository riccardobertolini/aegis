"""Repository implementations — all concrete SQLite adapters."""
from backend.infrastructure.adapters.repositories.assistant_repo import AssistantRepository
from backend.infrastructure.adapters.repositories.audit_repo import AuditLogRepository
from backend.infrastructure.adapters.repositories.backup_repo import BackupRepository
from backend.infrastructure.adapters.repositories.base_sqlite import BaseSQLiteRepository
from backend.infrastructure.adapters.repositories.dataset_repo import DatasetRepository
from backend.infrastructure.adapters.repositories.document_repo import DocumentRepository
from backend.infrastructure.adapters.repositories.knowledge_repo import (
    CategoryRepository,
    KnowledgeBaseRepository,
)
from backend.infrastructure.adapters.repositories.memory_repo import MemoryRepository
from backend.infrastructure.adapters.repositories.model_repo import ModelRepository
from backend.infrastructure.adapters.repositories.role_repo import (
    PermissionRepository,
    RoleRepository,
)
from backend.infrastructure.adapters.repositories.user_repo import UserRepository
from backend.infrastructure.adapters.repositories.version_repo import VersionRepository
from backend.infrastructure.adapters.repositories.workflow_repo import WorkflowRepository

__all__ = [
    "AssistantRepository",
    "AuditLogRepository",
    "BackupRepository",
    "BaseSQLiteRepository",
    "CategoryRepository",
    "DatasetRepository",
    "DocumentRepository",
    "KnowledgeBaseRepository",
    "MemoryRepository",
    "ModelRepository",
    "PermissionRepository",
    "RoleRepository",
    "UserRepository",
    "VersionRepository",
    "WorkflowRepository",
]
