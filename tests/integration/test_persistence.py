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
from backend.infrastructure.adapters.repositories.audit_repo import AuditLogRepository
from backend.infrastructure.adapters.repositories.document_repo import DocumentRepository
from backend.infrastructure.adapters.repositories.knowledge_repo import (
    CategoryRepository,
    KnowledgeBaseRepository,
)
from backend.infrastructure.adapters.repositories.model_repo import ModelRepository
from backend.infrastructure.adapters.repositories.role_repo import RoleRepository
from backend.infrastructure.adapters.repositories.user_repo import UserRepository
from backend.infrastructure.adapters.repositories.version_repo import VersionRepository


@pytest_asyncio.fixture
async def session():
    """In-memory async SQLite session for isolation."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)
    factory = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as s:
        yield s
    await engine.dispose()


# ------------------------------------------------------------------ Role

@pytest.mark.asyncio
async def test_role_create_and_find(session):
    from backend.domain.models import Role
    repo = RoleRepository(session)
    role = Role(name="admin", description="Super-admin role")
    created = await repo.create(role)
    assert created.id is not None
    found = await repo.find_by_name("admin")
    assert found is not None
    assert found.name == "admin"


@pytest.mark.asyncio
async def test_role_list_all_active(session):
    from backend.domain.models import Role
    repo = RoleRepository(session)
    await repo.create(Role(name="editor", is_active=True))
    await repo.create(Role(name="viewer", is_active=False))
    active = await repo.find_all_active(session)
    names = [r.name for r in active]
    assert "editor" in names
    assert "viewer" not in names


# ------------------------------------------------------------------ User

@pytest.mark.asyncio
async def test_user_crud(session):
    from backend.domain.models import User
    repo = UserRepository(session)
    user = User(username="alice", hashed_password="hash_xyz")
    created = await repo.create(user)
    assert created.username == "alice"
    found = await repo.find_by_username("alice")
    assert found is not None
    assert found.id == created.id
    await repo.delete(created.id)
    gone = await repo.find_by_id(created.id)
    assert gone is None


# ---------------------------------------------------------- KnowledgeBase

@pytest.mark.asyncio
async def test_knowledge_base_create_and_category(session):
    from backend.domain.models import Category, KnowledgeBase
    kb_repo = KnowledgeBaseRepository(session)
    cat_repo = CategoryRepository(session)
    kb = await kb_repo.create(KnowledgeBase(name="Finance KB"))
    assert kb.id is not None
    await cat_repo.create(
        Category(name="Invoices", knowledge_base_id=kb.id)
    )
    cats = await cat_repo.find_by_knowledge_base(kb.id)
    assert len(cats) == 1
    assert cats[0].name == "Invoices"


# ------------------------------------------------------------------ Document

@pytest.mark.asyncio
async def test_document_create_and_search(session):
    from backend.domain.models import Document
    repo = DocumentRepository(session)
    doc = Document(
        filename="report_2024.pdf",
        original_filename="Annual Report 2024.pdf",
        storage_path="/data/documents/report_2024.pdf",
        sha256="abc123",
    )
    created = await repo.create(doc)
    found = await repo.find_by_sha256("abc123")
    assert found is not None
    assert found.id == created.id


# ------------------------------------------------------------------ Model

@pytest.mark.asyncio
async def test_model_create_and_activate(session):
    from backend.domain.models import AegisModel
    repo = ModelRepository(session)
    m = AegisModel(
        name="mamba-1.4b",
        architecture="mamba-ssm",
        storage_path="/models/mamba-1.4b",
    )
    created = await repo.create(m)
    assert created.is_active is False
    active = await repo.find_active(session)
    assert active is None  # Not active yet


# ------------------------------------------------------------------ AuditLog

@pytest.mark.asyncio
async def test_audit_log_append_and_list(session):
    from backend.domain.models import AuditLogEntry
    repo = AuditLogRepository(session)
    for action in ["login", "login", "logout"]:
        await repo.create(
            AuditLogEntry(actor_id="user-1", action=action, resource="auth")
        )
    entries = await repo.find_by_actor("user-1")
    assert len(entries) == 3
    logins = await repo.find_by_action("login")
    assert len(logins) == 2


# ------------------------------------------------------------------ Version

@pytest.mark.asyncio
async def test_version_create_and_latest(session):
    import json
    from uuid import uuid4

    from backend.domain.models import Version
    repo = VersionRepository(session)
    eid = uuid4()
    for num in [1, 2, 3]:
        await repo.create(
            Version(
                entity_type="assistant",
                entity_id=str(eid),
                version_number=num,
                snapshot_json=json.dumps({"v": num}),
            )
        )
    latest = await repo.find_latest("assistant", str(eid))
    assert latest is not None
    assert latest.version_number == 3
    all_versions = await repo.find_by_entity("assistant", eid)
    assert len(all_versions) == 3
