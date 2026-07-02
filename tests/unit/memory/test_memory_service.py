"""Unit tests — MemoryService."""
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.domain.ports.memory import MemoryEntry, MemoryRole, SessionSummary
from backend.infrastructure.memory.service import MemoryService


def _make_session():
    """Return a mock AsyncSession that supports add/delete/commit/get/execute."""
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.delete = AsyncMock()

    turns = []

    async def _execute(stmt, *a, **kw):
        result = MagicMock()
        result.scalars.return_value.all.return_value = turns
        result.all.return_value = [(t.session_id,) for t in turns]
        result.description = [("session_id",)]
        return result

    session.execute = _execute
    return session, turns


@pytest.mark.asyncio
async def test_append_adds_record():
    session, _ = _make_session()
    svc = MemoryService(session)
    entry = MemoryEntry(
        session_id="s1", role=MemoryRole.USER, content="hello",
        timestamp=datetime.now(timezone.utc),
    )
    await svc.append(entry)
    session.add.assert_called_once()
    session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_get_history_returns_entries():
    from backend.infrastructure.memory.models import ConversationTurnRecord
    session, turns = _make_session()
    now = datetime.now(timezone.utc)
    turns.append(
        ConversationTurnRecord(
            session_id="s1", role="user", content="hi",
            metadata_json="{}", timestamp=now,
        )
    )
    svc = MemoryService(session)
    result = await svc.get_history("s1", last_n=5)
    assert len(result) == 1
    assert result[0].content == "hi"
    assert result[0].role == MemoryRole.USER


@pytest.mark.asyncio
async def test_summarize_extractive_fallback():
    session, _ = _make_session()
    from backend.infrastructure.memory.models import ConversationTurnRecord
    from datetime import timezone
    turns_list = [
        ConversationTurnRecord(session_id="s1", role="user", content="What is AI?",
                               metadata_json="{}", timestamp=datetime.now(timezone.utc)),
        ConversationTurnRecord(session_id="s1", role="assistant", content="AI is intelligence.",
                               metadata_json="{}", timestamp=datetime.now(timezone.utc)),
    ]

    async def _execute(stmt, *a, **kw):
        result = MagicMock()
        result.scalars.return_value.all.return_value = turns_list
        return result

    session.execute = _execute
    session.get = AsyncMock(return_value=None)

    svc = MemoryService(session, summariser=None)
    summary = await svc.summarize_session("s1")
    assert "AI" in summary
    assert "2 turns" in summary or "2" in summary


def test_extractive_summary_content():
    from backend.infrastructure.memory.models import ConversationTurnRecord
    from datetime import timezone
    entries = [
        MemoryEntry(session_id="s1", role=MemoryRole.USER, content="Ciao",
                    timestamp=datetime.now(timezone.utc)),
        MemoryEntry(session_id="s1", role=MemoryRole.ASSISTANT, content="Risposta.",
                    timestamp=datetime.now(timezone.utc)),
    ]
    summary = MemoryService._extractive_summary(entries)
    assert "Ciao" in summary
    assert "Risposta" in summary
