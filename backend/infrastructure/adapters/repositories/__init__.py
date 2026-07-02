"""Repository package — re-exports all SQLite repository classes."""
from backend.infrastructure.adapters.repositories.assistant_repo import SQLiteAssistantRepository, AssistantRepository
from backend.infrastructure.adapters.repositories.audit_repo import SQLiteAuditLogRepository, AuditLogRepository
from backend.infrastructure.adapters.repositories.backup_repo import SQLiteBackupRepository, BackupRepository
from backend.infrastructure.adapters.repositories.document_repo import (
    SQLiteDocumentRepository, DocumentRepository,
    SQLiteCategoryRepository, CategoryRepository,
    SQLiteKnowledgeBaseRepository, KnowledgeBaseRepository,
)
from backend.infrastructure.adapters.repositories.memory_repo import SQLiteMemoryEntryRepository, MemoryEntryRepository
from backend.infrastructure.adapters.repositories.model_repo import (
    SQLiteModelRecordRepository, ModelRecordRepository,
    SQLiteDatasetRepository, DatasetRepository,
)
from backend.infrastructure.adapters.repositories.user_repo import (
    SQLiteUserRepository, UserRepository,
    SQLiteRoleRepository, RoleRepository,
    SQLitePermissionRepository, PermissionRepository,
)
from backend.infrastructure.adapters.repositories.workflow_repo import (
    SQLiteWorkflowRepository, WorkflowRepository,
    SQLiteRuleRepository, RuleRepository,
)

__all__ = [
    "SQLiteAssistantRepository", "AssistantRepository",
    "SQLiteAuditLogRepository", "AuditLogRepository",
    "SQLiteBackupRepository", "BackupRepository",
    "SQLiteDocumentRepository", "DocumentRepository",
    "SQLiteCategoryRepository", "CategoryRepository",
    "SQLiteKnowledgeBaseRepository", "KnowledgeBaseRepository",
    "SQLiteMemoryEntryRepository", "MemoryEntryRepository",
    "SQLiteModelRecordRepository", "ModelRecordRepository",
    "SQLiteDatasetRepository", "DatasetRepository",
    "SQLiteUserRepository", "UserRepository",
    "SQLiteRoleRepository", "RoleRepository",
    "SQLitePermissionRepository", "PermissionRepository",
    "SQLiteWorkflowRepository", "WorkflowRepository",
    "SQLiteRuleRepository", "RuleRepository",
]
