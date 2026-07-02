"""Integration tests — local SQLite persistence layer.

All tests run against an in-memory SQLite database (no file I/O required).
No cloud, no network, no external service is touched.
"""
from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

# Import all models so SQLModel.metadata is populated
import backend.domain.models  # noqa: F401

from backend.infrastructure.adapters.repositories.assistant_repo import AssistantRepository
from backend.infrastructure.adapters.repositories.user_repo import UserRepository
from backend.infrastructure.adapters.repositories.role_repo import RoleRepository
from backend.infrastructure.adapters.repositories.document_repo import DocumentRepository
from backend.infrastructure.adapters.repositories.knowledge_repo import KnowledgeBaseRepository, CategoryRepository
from backend.infrastructure.adapters.repositories.model_repo import ModelRepository
from backend.infrastructure.adapters.repositories.audit_repo import AuditLogRepository
from backend.infrastructure.adapters.repositories.version_repo import VersionRepository


@pytest_asyncio.fixture
async def session():
    """In-memory async SQLite session for isolation."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    factory = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as s:
        yield s
    await engine.dispose()


# ------------------------------------------------------------------ Role

@pytest.mark.asyncio
async def test_role_create_and_find(session):
    from backend.domain.models import Role
    repo = RoleRepository()
    role = Role(name="admin", description="Super-admin role")
    created = await repo.create(role, session)
    assert created.id is not None
    found = await repo.find_by_name("admin", session)
    assert found is not None
    assert found.name == "admin"


@pytest.mark.asyncio
async def test_role_list_all_active(session):
    from backend.domain.models import Role
    repo = RoleRepository()
    await repo.create(Role(name="editor", is_active=True), session)
    await repo.create(Role(name="viewer", is_active=False), session)
    active = await repo.find_all_active(session)
    names = [r.name for r in active]
    assert "editor" in names
    assert "viewer" not in names


# ------------------------------------------------------------------ User

@pytest.mark.asyncio
async def test_user_crud(session):
    from backend.domain.models import User
    repo = UserRepository()
    user = User(username="alice", hashed_password="hash_xyz")
    created = await repo.create(user, session)
    assert created.username == "alice"
    found = await repo.find_by_username("alice", session)
    assert found is not None
    assert found.id == created.id
    await repo.delete(created.id, session)
    gone = await repo.find_by_id(created.id, session)
    assert gone is None


# ---------------------------------------------------------- KnowledgeBase

@pytest.mark.asyncio
async def test_knowledge_base_create_and_category(session):
    from backend.domain.models import Category, KnowledgeBase
    kb_repo = KnowledgeBaseRepository()
    cat_repo = CategoryRepository()
    kb = await kb_repo.create(KnowledgeBase(name="Finance KB"), session)
    assert kb.id is not None
    cat = await cat_repo.create(
        Category(name="Invoices", knowledge_base_id=kb.id), session
    )
    cats = await cat_repo.find_by_knowledge_base(kb.id, session)
    assert len(cats) == 1
    assert cats[0].name == "Invoices"


# ------------------------------------------------------------------ Document

@pytest.mark.asyncio
async def test_document_create_and_search(session):
    from backend.domain.models import Document
    repo = DocumentRepository()
    doc = Document(
        filename="report_2024.pdf",
        original_filename="Annual Report 2024.pdf",
        storage_path="/data/documents/report_2024.pdf",
        sha256="abc123",
    )
    created = await repo.create(doc, session)
    found = await repo.find_by_sha256("abc123", session)
    assert found is not None
    assert found.id == created.id


# ------------------------------------------------------------------ Model

@pytest.mark.asyncio
async def test_model_create_and_activate(session):
    from backend.domain.models import AegisModel
    repo = ModelRepository()
    m = AegisModel(
        name="mamba-1.4b",
        architecture="mamba-ssm",
        storage_path="/models/mamba-1.4b",
    )
    created = await repo.create(m, session)
    assert created.is_active is False
    active = await repo.find_active(session)
    assert active is None  # Not active yet


# ------------------------------------------------------------------ AuditLog

@pytest.mark.asyncio
async def test_audit_log_append_and_list(session):
    from backend.domain.models import AuditLogEntry
    repo = AuditLogRepository()
    for action in ["login", "login", "logout"]:
        await repo.create(
            AuditLogEntry(actor_id="user-1", action=action, resource="auth"),
            session,
        )
    entries = await repo.find_by_actor("user-1", session)
    assert len(entries) == 3
    logins = await repo.find_by_action("login", session)
    assert len(logins) == 2


# ------------------------------------------------------------------ Version

@pytest.mark.asyncio
async def test_version_create_and_latest(session):
    from uuid import uuid4
    from backend.domain.models import Version
    import json
    repo = VersionRepository()
    eid = uuid4()
    for num in [1, 2, 3]:
        await repo.create(
            Version(
                entity_type="assistant",
                entity_id=str(eid),
                version_number=num,
                snapshot_json=json.dumps({"v": num}),
            ),
            session,
        )
    latest = await repo.find_latest("assistant", eid, session)
    assert latest is not None
    assert latest.version_number == 3
    all_versions = await repo.find_by_entity("assistant", eid, session)
    assert len(all_versions) == 3
