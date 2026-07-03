"""Unit tests — MemoryEngine."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.domain.ports.memory import MemoryEntry
from backend.infrastructure.adapters.memory.memory_engine import (
    MemoryEngine,
    _extractive_summary,
)


@pytest.fixture
def tmp_settings(tmp_path):
    from backend.shared.config import Settings
    s = MagicMock(spec=Settings)
    s.db_path = tmp_path / "test_memory.db"
    return s


@pytest.fixture
def engine(tmp_settings):
    return MemoryEngine(settings=tmp_settings)


def run(coro):
    return asyncio.run(coro)


class TestMemoryEngine:
    def test_append_and_get_history(self, engine):
        e1 = MemoryEntry("s1", "user", "Hello")
        e2 = MemoryEntry("s1", "assistant", "Hi there")
        run(engine.append(e1))
        run(engine.append(e2))
        hist = run(engine.get_history("s1", last_n=10))
        assert len(hist) == 2
        assert hist[0].role == "user"
        assert hist[1].content == "Hi there"

    def test_clear_session(self, engine):
        run(engine.append(MemoryEntry("s2", "user", "test")))
        run(engine.clear_session("s2"))
        hist = run(engine.get_history("s2"))
        assert hist == []

    def test_separate_sessions(self, engine):
        run(engine.append(MemoryEntry("sx", "user", "msgX")))
        run(engine.append(MemoryEntry("sy", "user", "msgY")))
        hx = run(engine.get_history("sx"))
        hy = run(engine.get_history("sy"))
        assert all(e.session_id == "sx" for e in hx)
        assert all(e.session_id == "sy" for e in hy)

    def test_extractive_summary_short(self):
        text = "Hello world. This is a test."
        result = _extractive_summary(text, max_sentences=8)
        assert "test" in result

    def test_extractive_summary_long(self):
        sentences = [f"Sentence number {i} about the aegis system." for i in range(20)]
        text = " ".join(sentences)
        result = _extractive_summary(text, max_sentences=5)
        assert len(result) < len(text)

    def test_summarize_session_no_ai(self, engine):
        for i in range(5):
            run(engine.append(MemoryEntry("s3", "user", f"Message {i} about topic foo")))
        summary = run(engine.summarize_session("s3"))
        assert isinstance(summary, str)
        assert len(summary) > 0

    def test_summarize_session_with_ai(self, engine):
        mock_ai = AsyncMock()
        mock_ai.complete.return_value = "AI summary here"
        engine._core_ai = mock_ai
        run(engine.append(MemoryEntry("s4", "user", "Test message")))
        summary = run(engine.summarize_session("s4"))
        assert summary == "AI summary here"
        mock_ai.complete.assert_called_once()

    def test_list_sessions(self, engine):
        run(engine.append(MemoryEntry("sa", "user", "a")))
        run(engine.append(MemoryEntry("sb", "user", "b")))
        sessions = run(engine.list_sessions())
        assert "sa" in sessions
        assert "sb" in sessions
