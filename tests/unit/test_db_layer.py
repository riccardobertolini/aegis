"""Unit tests for Fase 2 — DB layer.

Uses an in-memory SQLite database so no file I/O is needed.
All tests are fully offline-first: no network, no external services.
"""
from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

import backend.infrastructure.database.models  # noqa: F401 — populate metadata
from backend.infrastructure.adapters.repositories.audit_repo import SQLiteAuditLogRepository
from backend.infrastructure.adapters.repositories.document_repo import SQLiteDocumentRepository
from backend.infrastructure.adapters.repositories.memory_repo import SQLiteMemoryEntryRepository
from backend.infrastructure.adapters.repositories.model_repo import SQLiteModelRecordRepository
from backend.infrastructure.adapters.repositories.user_repo import (
    SQLiteRoleRepository,
    SQLiteUserRepository,
)
from backend.infrastructure.database.models import (
    AuditLogModel,
    DocumentModel,
    MemoryEntryModel,
    ModelRecordModel,
    RoleModel,
    UserModel,
)

IN_MEMORY_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine(IN_MEMORY_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.drop_all)
        await conn.run_sync(SQLModel.metadata.create_all)
    factory = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as s:
        yield s
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    await engine.dispose()


# ---------------------------------------------------------------------------
# UserModel
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_user_create_and_get(session: AsyncSession) -> None:
    repo = SQLiteUserRepository(session)
    user = UserModel(
        id=str(uuid4()), username="alice", email="alice@local",
        hashed_password="xxx", role_ids_json="[]",
        created_at=datetime.now(tz=UTC),
        updated_at=datetime.now(tz=UTC),
    )
    created = await repo.create(user)
    assert created.id == user.id

    fetched = await repo.get(user.id)
    assert fetched is not None
    assert fetched.username == "alice"


@pytest.mark.asyncio
async def test_user_find_by_username(session: AsyncSession) -> None:
    repo = SQLiteUserRepository(session)
    user = UserModel(
        id=str(uuid4()), username="bob", email="bob@local",
        hashed_password="yyy", role_ids_json="[]",
        created_at=datetime.now(tz=UTC),
        updated_at=datetime.now(tz=UTC),
    )
    await repo.create(user)
    found = await repo.find_by_username("bob")
    assert found is not None
    assert found.email == "bob@local"


@pytest.mark.asyncio
async def test_user_find_by_username_missing(session: AsyncSession) -> None:
    repo = SQLiteUserRepository(session)
    assert await repo.find_by_username("nobody") is None


@pytest.mark.asyncio
async def test_user_update(session: AsyncSession) -> None:
    repo = SQLiteUserRepository(session)
    user = UserModel(
        id=str(uuid4()), username="charlie", email="charlie@local",
        hashed_password="zzz", role_ids_json="[]",
        created_at=datetime.now(tz=UTC),
        updated_at=datetime.now(tz=UTC),
    )
    await repo.create(user)
    user.is_active = False
    updated = await repo.update(user)
    assert updated.is_active is False


@pytest.mark.asyncio
async def test_user_delete(session: AsyncSession) -> None:
    repo = SQLiteUserRepository(session)
    uid = str(uuid4())
    user = UserModel(
        id=uid, username="dave", email="dave@local",
        hashed_password="aaa", role_ids_json="[]",
        created_at=datetime.now(tz=UTC),
        updated_at=datetime.now(tz=UTC),
    )
    await repo.create(user)
    deleted = await repo.delete(uid)
    assert deleted is True
    assert await repo.get(uid) is None


@pytest.mark.asyncio
async def test_user_delete_nonexistent(session: AsyncSession) -> None:
    repo = SQLiteUserRepository(session)
    assert await repo.delete("nonexistent") is False


# ---------------------------------------------------------------------------
# RoleModel
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_role_create_and_find_by_name(session: AsyncSession) -> None:
    repo = SQLiteRoleRepository(session)
    role = RoleModel(
        id=str(uuid4()), name="admin", permissions_json="[]",
        created_at=datetime.now(tz=UTC),
        updated_at=datetime.now(tz=UTC),
    )
    await repo.create(role)
    found = await repo.find_by_name("admin")
    assert found is not None
    assert found.name == "admin"


# ---------------------------------------------------------------------------
# DocumentModel
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_document_find_by_status(session: AsyncSession) -> None:
    repo = SQLiteDocumentRepository(session)
    for i in range(3):
        doc = DocumentModel(
            id=str(uuid4()), owner_id="user1", status="pending",
            filename=f"file{i}.txt",
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )
        await repo.create(doc)
    pending = await repo.find_by_status("pending")
    assert len(pending) == 3


@pytest.mark.asyncio
async def test_document_find_by_checksum(session: AsyncSession) -> None:
    repo = SQLiteDocumentRepository(session)
    doc = DocumentModel(
        id=str(uuid4()), owner_id="user1", checksum_sha256="abc123",
        created_at=datetime.now(tz=UTC),
        updated_at=datetime.now(tz=UTC),
    )
    await repo.create(doc)
    found = await repo.find_by_checksum("abc123")
    assert found is not None
    assert found.id == doc.id


# ---------------------------------------------------------------------------
# MemoryEntryModel
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_memory_find_by_session(session: AsyncSession) -> None:
    repo = SQLiteMemoryEntryRepository(session)
    sid = "session-42"
    for _ in range(5):
        entry = MemoryEntryModel(
            id=str(uuid4()), session_id=sid,
            assistant_id="ast1", user_id="u1",
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )
        await repo.create(entry)
    entries = await repo.find_by_session(sid)
    assert len(entries) == 5


@pytest.mark.asyncio
async def test_memory_delete_by_session(session: AsyncSession) -> None:
    repo = SQLiteMemoryEntryRepository(session)
    sid = "session-del"
    for _ in range(3):
        entry = MemoryEntryModel(
            id=str(uuid4()), session_id=sid,
            assistant_id="ast1", user_id="u1",
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )
        await repo.create(entry)
    count = await repo.delete_by_session(sid)
    assert count == 3
    assert len(await repo.find_by_session(sid)) == 0


# ---------------------------------------------------------------------------
# AuditLogModel — immutability
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_audit_append_only(session: AsyncSession) -> None:
    repo = SQLiteAuditLogRepository(session)
    entry = AuditLogModel(
        id=str(uuid4()), actor_id="u1", action="login",
        resource_type="session", resource_id="s1",
        created_at=datetime.now(tz=UTC),
        updated_at=datetime.now(tz=UTC),
    )
    created = await repo.create(entry)
    assert created.id == entry.id

    with pytest.raises(NotImplementedError):
        await repo.update(entry)

    with pytest.raises(NotImplementedError):
        await repo.delete(entry.id)


@pytest.mark.asyncio
async def test_audit_find_by_actor(session: AsyncSession) -> None:
    repo = SQLiteAuditLogRepository(session)
    for _ in range(4):
        await repo.create(AuditLogModel(
            id=str(uuid4()), actor_id="actor1",
            action="query", resource_type="kb", resource_id="kb1",
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        ))
    logs = await repo.find_by_actor("actor1")
    assert len(logs) == 4


# ---------------------------------------------------------------------------
# ModelRecordModel
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_model_record_find_available(session: AsyncSession) -> None:
    repo = SQLiteModelRecordRepository(session)
    await repo.create(ModelRecordModel(
        id=str(uuid4()), name="mamba-130m", status="available",
        created_at=datetime.now(tz=UTC),
        updated_at=datetime.now(tz=UTC),
    ))
    await repo.create(ModelRecordModel(
        id=str(uuid4()), name="mamba-370m", status="unavailable",
        created_at=datetime.now(tz=UTC),
        updated_at=datetime.now(tz=UTC),
    ))
    available = await repo.find_available()
    assert len(available) == 1
    assert available[0].name == "mamba-130m"
