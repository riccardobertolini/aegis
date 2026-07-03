"""Repository package — re-exports all SQLite repository classes."""
from backend.infrastructure.adapters.repositories.assistant_repo import (
    AssistantRepository,
    SQLiteAssistantRepository,
)
from backend.infrastructure.adapters.repositories.audit_repo import (
    AuditLogRepository,
    SQLiteAuditLogRepository,
)
from backend.infrastructure.adapters.repositories.backup_repo import (
    BackupRepository,
    SQLiteBackupRepository,
)
from backend.infrastructure.adapters.repositories.document_repo import (
    CategoryRepository,
    DocumentRepository,
    KnowledgeBaseRepository,
    SQLiteCategoryRepository,
    SQLiteDocumentRepository,
    SQLiteKnowledgeBaseRepository,
)
from backend.infrastructure.adapters.repositories.memory_repo import (
    MemoryEntryRepository,
    SQLiteMemoryEntryRepository,
)
from backend.infrastructure.adapters.repositories.model_repo import (
    DatasetRepository,
    ModelRecordRepository,
    SQLiteDatasetRepository,
    SQLiteModelRecordRepository,
)
from backend.infrastructure.adapters.repositories.user_repo import (
    PermissionRepository,
    RoleRepository,
    SQLitePermissionRepository,
    SQLiteRoleRepository,
    SQLiteUserRepository,
    UserRepository,
)
from backend.infrastructure.adapters.repositories.workflow_repo import (
    RuleRepository,
    SQLiteRuleRepository,
    SQLiteWorkflowRepository,
    WorkflowRepository,
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
