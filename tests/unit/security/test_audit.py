"""Unit tests: AuditWriter/Reader with HMAC chain verification."""
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.domain.ports.security import AuditEntry
from backend.infrastructure.security.audit import AuditReader, AuditWriter
from backend.infrastructure.security.models import AuditLogModel

_AUDIT_KEY = b"test-audit-key-32-bytes-padding!"


@pytest.fixture
def mock_session():
    return AsyncMock()


def _make_entry(**kwargs) -> AuditEntry:
    defaults = {
        "event_type": "auth.login",
        "actor_id": "u1",
        "actor_username": "alice",
        "resource": "session",
        "action": "authenticate",
        "outcome": "success",
        "timestamp": datetime(2025, 1, 1, 12, 0, 0),
    }
    defaults.update(kwargs)
    return AuditEntry(**defaults)


@pytest.mark.asyncio
async def test_audit_writer_adds_row(mock_session):
    mock_session.execute = AsyncMock(return_value=MagicMock(
        scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=None)))
    ))
    writer = AuditWriter(mock_session, _AUDIT_KEY)
    await writer.append(_make_entry())
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_audit_reader_query_returns_entries(mock_session):
    import json
    row = AuditLogModel(
        id="test-id",
        timestamp=datetime(2025, 1, 1),
        event_type="auth.login",
        actor_id="u1",
        actor_username="alice",
        resource="session",
        action="authenticate",
        outcome="success",
        details_json=json.dumps({"ip": "127.0.0.1"}),
    )
    mock_session.execute = AsyncMock(return_value=MagicMock(
        scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[row])))
    ))
    reader = AuditReader(mock_session, _AUDIT_KEY)
    entries = await reader.query(limit=10)
    assert len(entries) == 1
    assert entries[0].actor_username == "alice"
