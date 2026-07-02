"""Bidirectional mappers: ORM model <-> domain entity."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from backend.domain.entities.assistant import Assistant, AssistantConfig
from backend.domain.entities.audit import AuditLog
from backend.domain.entities.backup import Backup, BackupStatus
from backend.domain.entities.document import Category, Document, DocumentStatus, KnowledgeBase
from backend.domain.entities.memory import MemoryEntry
from backend.domain.entities.model import Dataset, ModelRecord, ModelStatus, ModelType
from backend.domain.entities.user import Permission, Role, User
from backend.domain.entities.workflow import Rule, Workflow, WorkflowStatus, WorkflowStep
from backend.infrastructure.database.models import (
    AssistantModel, AuditLogModel, BackupModel, CategoryModel,
    DatasetModel, DocumentModel, KnowledgeBaseModel, MemoryEntryModel,
    ModelRecordModel, PermissionModel, RoleModel, RuleModel,
    UserModel, WorkflowModel,
)


def _dt(v) -> datetime:
    if isinstance(v, datetime):
        return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
    return datetime.fromisoformat(str(v)).replace(tzinfo=timezone.utc)


# --- Permission ---

def permission_to_orm(e: Permission) -> PermissionModel:
    return PermissionModel(id=e.id, name=e.name, description=e.description,
                           resource=e.resource, action=e.action,
                           created_at=_dt(e.created_at), updated_at=_dt(e.updated_at))

def orm_to_permission(m: PermissionModel) -> Permission:
    p = Permission.__new__(Permission)
    p.id, p.name, p.description = m.id, m.name, m.description
    p.resource, p.action = m.resource, m.action
    p.created_at, p.updated_at = _dt(m.created_at), _dt(m.updated_at)
    return p


# --- Role ---

def role_to_orm(e: Role) -> RoleModel:
    m = RoleModel(id=e.id, name=e.name, description=e.description,
                  created_at=_dt(e.created_at), updated_at=_dt(e.updated_at))
    m.set_permissions(e.permissions)
    return m

def orm_to_role(m: RoleModel) -> Role:
    r = Role.__new__(Role)
    r.id, r.name, r.description = m.id, m.name, m.description
    r.permissions = m.get_permissions()
    r.created_at, r.updated_at = _dt(m.created_at), _dt(m.updated_at)
    return r


# --- User ---

def user_to_orm(e: User) -> UserModel:
    return UserModel(
        id=e.id, username=e.username, email=e.email,
        hashed_password=e.hashed_password,
        role_ids_json=json.dumps(e.role_ids),
        is_active=e.is_active, is_superadmin=e.is_superadmin,
        last_login_at=e.last_login_at,
        created_at=_dt(e.created_at), updated_at=_dt(e.updated_at),
    )

def orm_to_user(m: UserModel) -> User:
    u = User.__new__(User)
    u.id, u.username, u.email = m.id, m.username, m.email
    u.hashed_password = m.hashed_password
    u.role_ids = json.loads(m.role_ids_json)
    u.is_active, u.is_superadmin = m.is_active, m.is_superadmin
    u.last_login_at = m.last_login_at
    u.created_at, u.updated_at = _dt(m.created_at), _dt(m.updated_at)
    return u


# --- Assistant ---

def assistant_to_orm(e: Assistant) -> AssistantModel:
    return AssistantModel(
        id=e.id, name=e.name, description=e.description, owner_id=e.owner_id,
        config_json=json.dumps({
            "model_id": e.config.model_id,
            "system_prompt": e.config.system_prompt,
            "temperature": e.config.temperature,
            "max_tokens": e.config.max_tokens,
            "feature_flags": e.config.feature_flags,
            "extra": e.config.extra,
        }),
        is_active=e.is_active, version=e.version,
        knowledge_base_ids_json=json.dumps(e.knowledge_base_ids),
        plugin_ids_json=json.dumps(e.plugin_ids),
        created_at=_dt(e.created_at), updated_at=_dt(e.updated_at),
    )

def orm_to_assistant(m: AssistantModel) -> Assistant:
    a = Assistant.__new__(Assistant)
    a.id, a.name, a.description, a.owner_id = m.id, m.name, m.description, m.owner_id
    cfg = json.loads(m.config_json)
    a.config = AssistantConfig(
        model_id=cfg.get("model_id", ""),
        system_prompt=cfg.get("system_prompt", ""),
        temperature=cfg.get("temperature", 0.7),
        max_tokens=cfg.get("max_tokens", 2048),
        feature_flags=cfg.get("feature_flags", {}),
        extra=cfg.get("extra", {}),
    )
    a.is_active, a.version = m.is_active, m.version
    a.knowledge_base_ids = json.loads(m.knowledge_base_ids_json)
    a.plugin_ids = json.loads(m.plugin_ids_json)
    a.created_at, a.updated_at = _dt(m.created_at), _dt(m.updated_at)
    return a


# --- Category ---

def category_to_orm(e: Category) -> CategoryModel:
    return CategoryModel(id=e.id, name=e.name, description=e.description,
                         parent_id=e.parent_id,
                         created_at=_dt(e.created_at), updated_at=_dt(e.updated_at))

def orm_to_category(m: CategoryModel) -> Category:
    c = Category.__new__(Category)
    c.id, c.name, c.description, c.parent_id = m.id, m.name, m.description, m.parent_id
    c.created_at, c.updated_at = _dt(m.created_at), _dt(m.updated_at)
    return c


# --- Document ---

def document_to_orm(e: Document) -> DocumentModel:
    return DocumentModel(
        id=e.id, filename=e.filename, original_filename=e.original_filename,
        mime_type=e.mime_type, size_bytes=e.size_bytes,
        checksum_sha256=e.checksum_sha256, storage_path=e.storage_path,
        status=e.status.value, owner_id=e.owner_id,
        category_ids_json=json.dumps(e.category_ids),
        knowledge_base_ids_json=json.dumps(e.knowledge_base_ids),
        metadata_json=json.dumps(e.metadata),
        is_encrypted=e.is_encrypted,
        created_at=_dt(e.created_at), updated_at=_dt(e.updated_at),
    )

def orm_to_document(m: DocumentModel) -> Document:
    d = Document.__new__(Document)
    d.id, d.filename, d.original_filename = m.id, m.filename, m.original_filename
    d.mime_type, d.size_bytes = m.mime_type, m.size_bytes
    d.checksum_sha256, d.storage_path = m.checksum_sha256, m.storage_path
    d.status = DocumentStatus(m.status)
    d.owner_id = m.owner_id
    d.category_ids = json.loads(m.category_ids_json)
    d.knowledge_base_ids = json.loads(m.knowledge_base_ids_json)
    d.metadata = json.loads(m.metadata_json)
    d.is_encrypted = m.is_encrypted
    d.created_at, d.updated_at = _dt(m.created_at), _dt(m.updated_at)
    return d


# --- KnowledgeBase ---

def kb_to_orm(e: KnowledgeBase) -> KnowledgeBaseModel:
    return KnowledgeBaseModel(
        id=e.id, name=e.name, description=e.description, owner_id=e.owner_id,
        category_ids_json=json.dumps(e.category_ids),
        is_active=e.is_active, chroma_collection_name=e.chroma_collection_name,
        created_at=_dt(e.created_at), updated_at=_dt(e.updated_at),
    )

def orm_to_kb(m: KnowledgeBaseModel) -> KnowledgeBase:
    kb = KnowledgeBase.__new__(KnowledgeBase)
    kb.id, kb.name, kb.description, kb.owner_id = m.id, m.name, m.description, m.owner_id
    kb.category_ids = json.loads(m.category_ids_json)
    kb.is_active, kb.chroma_collection_name = m.is_active, m.chroma_collection_name
    kb.created_at, kb.updated_at = _dt(m.created_at), _dt(m.updated_at)
    return kb


# --- MemoryEntry ---

def memory_to_orm(e: MemoryEntry) -> MemoryEntryModel:
    return MemoryEntryModel(
        id=e.id, session_id=e.session_id, assistant_id=e.assistant_id,
        user_id=e.user_id, role=e.role, content=e.content,
        embedding_id=e.embedding_id, metadata_json=json.dumps(e.metadata),
        is_encrypted=e.is_encrypted,
        created_at=_dt(e.created_at), updated_at=_dt(e.updated_at),
    )

def orm_to_memory(m: MemoryEntryModel) -> MemoryEntry:
    me = MemoryEntry.__new__(MemoryEntry)
    me.id, me.session_id, me.assistant_id = m.id, m.session_id, m.assistant_id
    me.user_id, me.role, me.content = m.user_id, m.role, m.content
    me.embedding_id = m.embedding_id
    me.metadata = json.loads(m.metadata_json)
    me.is_encrypted = m.is_encrypted
    me.created_at, me.updated_at = _dt(m.created_at), _dt(m.updated_at)
    return me


# --- ModelRecord ---

def model_to_orm(e: ModelRecord) -> ModelRecordModel:
    return ModelRecordModel(
        id=e.id, name=e.name, model_type=e.model_type.value,
        status=e.status.value, storage_path=e.storage_path,
        checksum_sha256=e.checksum_sha256, size_bytes=e.size_bytes,
        architecture=e.architecture, context_length=e.context_length,
        metadata_json=json.dumps(e.metadata),
        created_at=_dt(e.created_at), updated_at=_dt(e.updated_at),
    )

def orm_to_model(m: ModelRecordModel) -> ModelRecord:
    mr = ModelRecord.__new__(ModelRecord)
    mr.id, mr.name = m.id, m.name
    mr.model_type = ModelType(m.model_type)
    mr.status = ModelStatus(m.status)
    mr.storage_path, mr.checksum_sha256 = m.storage_path, m.checksum_sha256
    mr.size_bytes, mr.architecture, mr.context_length = m.size_bytes, m.architecture, m.context_length
    mr.metadata = json.loads(m.metadata_json)
    mr.created_at, mr.updated_at = _dt(m.created_at), _dt(m.updated_at)
    return mr


# --- Dataset ---

def dataset_to_orm(e: Dataset) -> DatasetModel:
    return DatasetModel(
        id=e.id, name=e.name, description=e.description,
        storage_path=e.storage_path, format=e.format,
        size_bytes=e.size_bytes, checksum_sha256=e.checksum_sha256,
        row_count=e.row_count, owner_id=e.owner_id,
        metadata_json=json.dumps(e.metadata),
        created_at=_dt(e.created_at), updated_at=_dt(e.updated_at),
    )

def orm_to_dataset(m: DatasetModel) -> Dataset:
    d = Dataset.__new__(Dataset)
    d.id, d.name, d.description = m.id, m.name, m.description
    d.storage_path, d.format = m.storage_path, m.format
    d.size_bytes, d.checksum_sha256, d.row_count = m.size_bytes, m.checksum_sha256, m.row_count
    d.owner_id = m.owner_id
    d.metadata = json.loads(m.metadata_json)
    d.created_at, d.updated_at = _dt(m.created_at), _dt(m.updated_at)
    return d


# --- Workflow ---

def workflow_to_orm(e: Workflow) -> WorkflowModel:
    return WorkflowModel(
        id=e.id, name=e.name, description=e.description, owner_id=e.owner_id,
        status=e.status.value,
        steps_json=json.dumps([{
            "step_id": s.step_id, "name": s.name,
            "engine": s.engine, "config": s.config,
            "next_step_id": s.next_step_id,
        } for s in e.steps]),
        metadata_json=json.dumps(e.metadata),
        created_at=_dt(e.created_at), updated_at=_dt(e.updated_at),
    )

def orm_to_workflow(m: WorkflowModel) -> Workflow:
    w = Workflow.__new__(Workflow)
    w.id, w.name, w.description, w.owner_id = m.id, m.name, m.description, m.owner_id
    w.status = WorkflowStatus(m.status)
    w.steps = [
        WorkflowStep(step_id=s["step_id"], name=s["name"],
                     engine=s["engine"], config=s["config"],
                     next_step_id=s.get("next_step_id"))
        for s in json.loads(m.steps_json)
    ]
    w.metadata = json.loads(m.metadata_json)
    w.created_at, w.updated_at = _dt(m.created_at), _dt(m.updated_at)
    return w


# --- Rule ---

def rule_to_orm(e: Rule) -> RuleModel:
    return RuleModel(
        id=e.id, name=e.name, description=e.description,
        resource=e.resource, condition_json=json.dumps(e.condition),
        action=e.action, priority=e.priority,
        is_active=e.is_active, owner_id=e.owner_id,
        created_at=_dt(e.created_at), updated_at=_dt(e.updated_at),
    )

def orm_to_rule(m: RuleModel) -> Rule:
    r = Rule.__new__(Rule)
    r.id, r.name, r.description = m.id, m.name, m.description
    r.resource, r.condition, r.action = m.resource, json.loads(m.condition_json), m.action
    r.priority, r.is_active, r.owner_id = m.priority, m.is_active, m.owner_id
    r.created_at, r.updated_at = _dt(m.created_at), _dt(m.updated_at)
    return r


# --- AuditLog ---

def audit_to_orm(e: AuditLog) -> AuditLogModel:
    return AuditLogModel(
        id=e.id, actor_id=e.actor_id, actor_username=e.actor_username,
        action=e.action, resource_type=e.resource_type, resource_id=e.resource_id,
        outcome=e.outcome, ip_address=e.ip_address,
        details_json=json.dumps(e.details),
        created_at=_dt(e.created_at), updated_at=_dt(e.updated_at),
    )

def orm_to_audit(m: AuditLogModel) -> AuditLog:
    a = AuditLog.__new__(AuditLog)
    a.id = m.id
    a.actor_id, a.actor_username = m.actor_id, m.actor_username
    a.action, a.resource_type, a.resource_id = m.action, m.resource_type, m.resource_id
    a.outcome, a.ip_address = m.outcome, m.ip_address
    a.details = json.loads(m.details_json)
    a.created_at, a.updated_at = _dt(m.created_at), _dt(m.updated_at)
    return a


# --- Backup ---

def backup_to_orm(e: Backup) -> BackupModel:
    return BackupModel(
        id=e.id, label=e.label, storage_path=e.storage_path,
        checksum_sha256=e.checksum_sha256, size_bytes=e.size_bytes,
        status=e.status.value, includes_json=json.dumps(e.includes),
        initiated_by=e.initiated_by, error_message=e.error_message,
        created_at=_dt(e.created_at), updated_at=_dt(e.updated_at),
    )

def orm_to_backup(m: BackupModel) -> Backup:
    b = Backup.__new__(Backup)
    b.id, b.label, b.storage_path = m.id, m.label, m.storage_path
    b.checksum_sha256, b.size_bytes = m.checksum_sha256, m.size_bytes
    b.status = BackupStatus(m.status)
    b.includes = json.loads(m.includes_json)
    b.initiated_by, b.error_message = m.initiated_by, m.error_message
    b.created_at, b.updated_at = _dt(m.created_at), _dt(m.updated_at)
    return b
