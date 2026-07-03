"""Unit tests for Administration Engine — service layer.

Uses an in-memory SQLite database so no file I/O is required.
"""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

import pytest
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.infrastructure.administration.service import AdministrationService

DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
async def engine():
    eng = create_async_engine(DB_URL, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest.fixture
def session_factory(engine):
    @asynccontextmanager
    async def _factory():
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as session:
            yield session
    return _factory


@pytest.fixture
def svc(session_factory, tmp_path):
    return AdministrationService(
        session_factory=session_factory,
        security_service=None,
        training_service=None,
        inference_container=None,
        models_root=tmp_path / "models",
        datasets_root=tmp_path / "datasets",
        experiments_root=tmp_path / "experiments",
        checkpoints_root=tmp_path / "checkpoints",
        backup_root=tmp_path / "backups",
    )


# ---------------------------------------------------------------------------
# Assistants
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_and_list_assistants(svc):
    a = await svc.create_assistant(name="Test Assistant", model_id="mamba-v1")
    assert a["id"] is not None
    assert a["name"] == "Test Assistant"
    listing = await svc.list_assistants()
    assert any(x["name"] == "Test Assistant" for x in listing)


@pytest.mark.asyncio
async def test_get_assistant(svc):
    a = await svc.create_assistant(name="GetTest")
    retrieved = await svc.get_assistant(a["id"])
    assert retrieved is not None
    assert retrieved["name"] == "GetTest"


@pytest.mark.asyncio
async def test_update_assistant(svc):
    a = await svc.create_assistant(name="Original")
    updated = await svc.update_assistant(a["id"], name="Updated")
    assert updated["name"] == "Updated"


@pytest.mark.asyncio
async def test_delete_assistant(svc):
    a = await svc.create_assistant(name="ToDelete")
    ok = await svc.delete_assistant(a["id"])
    assert ok is True
    assert await svc.get_assistant(a["id"]) is None


@pytest.mark.asyncio
async def test_duplicate_assistant(svc):
    a = await svc.create_assistant(name="Original", system_prompt="Hello")
    clone = await svc.duplicate_assistant(a["id"], new_name="Clone")
    assert clone is not None
    assert clone["name"] == "Clone"
    assert clone["system_prompt"] == "Hello"
    assert clone["id"] != a["id"]


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_and_list_templates(svc):
    t = await svc.create_template(name="TPL1", system_prompt="You are helpful.")
    assert t["id"] is not None
    listing = await svc.list_templates()
    assert any(x["name"] == "TPL1" for x in listing)


@pytest.mark.asyncio
async def test_delete_template(svc):
    t = await svc.create_template(name="DeleteMe")
    ok = await svc.delete_template(t["id"])
    assert ok is True


# ---------------------------------------------------------------------------
# Workflows
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_and_list_workflows(svc):
    w = await svc.create_workflow(name="WF1", steps='[{"step": 1}]')
    assert w["id"] is not None
    listing = await svc.list_workflows()
    assert any(x["name"] == "WF1" for x in listing)


@pytest.mark.asyncio
async def test_update_workflow(svc):
    w = await svc.create_workflow(name="WFUpdate")
    updated = await svc.update_workflow(w["id"], is_active=False)
    assert updated["is_active"] is False


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_and_list_rules(svc):
    r = await svc.create_rule(name="R1", condition='{"eq": ["lang", "it"]}', action='{"reply_in": "it"}')
    assert r["id"] is not None
    listing = await svc.list_rules()
    assert any(x["name"] == "R1" for x in listing)


# ---------------------------------------------------------------------------
# Feature toggles
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_feature_toggle(svc):
    await svc.set_feature("rag_enabled", True, "Enable RAG pipeline")
    assert await svc.is_feature_enabled("rag_enabled") is True
    await svc.set_feature("rag_enabled", False)
    assert await svc.is_feature_enabled("rag_enabled") is False


@pytest.mark.asyncio
async def test_feature_toggle_missing(svc):
    assert await svc.is_feature_enabled("nonexistent_feature") is False


# ---------------------------------------------------------------------------
# Language config
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_upsert_language(svc):
    lang = await svc.upsert_language("it", "Italiano", True, True)
    assert lang["code"] == "it"
    listing = await svc.list_languages()
    assert any(x["code"] == "it" for x in listing)


# ---------------------------------------------------------------------------
# Usage
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_record_and_query_usage(svc):
    await svc.record_usage(event_type="inference", user_id="u1", tokens_used=42, duration_ms=300)
    events = await svc.query_usage(event_type="inference", user_id="u1")
    assert any(e["tokens_used"] == 42 for e in events)


@pytest.mark.asyncio
async def test_usage_stats(svc):
    await svc.record_usage(event_type="training", tokens_used=100, duration_ms=500)
    stats = await svc.usage_stats(event_type="training")
    assert stats["total_events"] >= 1
    assert stats["total_tokens"] >= 100


# ---------------------------------------------------------------------------
# Config export / import
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_export_import_round_trip(svc):
    await svc.create_assistant(name="ExportTest", model_id="mamba-v1")
    exported = await svc.export_config()
    assert "assistants" in exported
    assert exported["export_version"] == "1"

    # Import into same svc (will create duplicates — acceptable in unit test)
    counts = await svc.import_config(exported)
    assert counts["assistants"] >= 1
