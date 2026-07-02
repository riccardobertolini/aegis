"""Unit tests — LogEngine."""
from __future__ import annotations

import asyncio
import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from backend.domain.ports.log_engine import LogEntry, LogQuery
from backend.infrastructure.adapters.log_engine.log_engine import LogEngine


@pytest.fixture
def tmp_settings(tmp_path):
    from backend.shared.config import Settings
    s = MagicMock(spec=Settings)
    s.duckdb_path = tmp_path / "test_log.duckdb"
    return s


@pytest.fixture
def engine(tmp_settings):
    return LogEngine(settings=tmp_settings)


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def _entry(msg, level="INFO", source="test"):
    return LogEntry(
        timestamp=datetime.utcnow(),
        level=level,
        message=msg,
        source=source,
    )


class TestLogEngine:
    def test_ingest_and_tail(self, engine):
        run(engine.ingest(_entry("Hello world")))
        run(engine.ingest(_entry("Second entry", level="WARNING")))
        entries = run(engine.tail(10))
        assert len(entries) == 2
        assert entries[-1].level == "WARNING"

    def test_query_by_level(self, engine):
        run(engine.ingest(_entry("info msg", level="INFO")))
        run(engine.ingest(_entry("error msg", level="ERROR")))
        results = run(engine.query(LogQuery(level="ERROR")))
        assert all(e.level == "ERROR" for e in results)

    def test_query_by_source(self, engine):
        run(engine.ingest(_entry("from svc_a", source="svc_a")))
        run(engine.ingest(_entry("from svc_b", source="svc_b")))
        results = run(engine.query(LogQuery(source="svc_a")))
        assert all("svc_a" in e.source for e in results)

    def test_severity_histogram(self, engine):
        for lvl in ["INFO", "INFO", "WARNING", "ERROR"]:
            run(engine.ingest(_entry("x", level=lvl)))
        hist = run(engine.severity_histogram())
        assert hist.get("INFO", 0) == 2
        assert hist.get("ERROR", 0) == 1

    def test_top_sources(self, engine):
        for _ in range(3):
            run(engine.ingest(_entry("x", source="heavy_source")))
        run(engine.ingest(_entry("x", source="light_source")))
        top = run(engine.top_sources(n=2))
        assert top[0][0] == "heavy_source"
        assert top[0][1] == 3

    def test_pattern_detection_oom(self, engine):
        run(engine.ingest(_entry("Java heap space: out of memory", level="ERROR")))
        run(engine.ingest(_entry("Normal operation")))
        patterns = run(engine.detect_patterns())
        names = [p["pattern"] for p in patterns]
        assert "OutOfMemory" in names

    def test_ingest_file_jsonl(self, engine, tmp_path):
        log_file = tmp_path / "sample.jsonl"
        lines = [
            json.dumps({"timestamp": "2025-01-01T00:00:00", "level": "INFO", "message": f"Line {i}", "source": "file_test"})
            for i in range(5)
        ]
        log_file.write_text("\n".join(lines))
        count = run(engine.ingest_file(log_file, fmt="jsonl"))
        assert count == 5
        entries = run(engine.query(LogQuery(source="file_test")))
        assert len(entries) == 5
