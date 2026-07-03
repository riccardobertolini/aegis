"""Unit tests — LogEngineService (in-memory DuckDB)."""

import pytest


def _try_import_duckdb():
    try:
        import duckdb
        return True
    except ImportError:
        return False


@pytest.mark.skipif(not _try_import_duckdb(), reason="duckdb not installed")
def test_log_and_query(tmp_path):
    from backend.infrastructure.log_engine.service import LogEngineService
    svc = LogEngineService(tmp_path / "logs.duckdb")
    svc.log("INFO", "test.event", component="test", session_id="s1", payload={"k": 1})
    svc.log("ERROR", "error.event", component="test")
    rows = svc.query(level="INFO", limit=10)
    assert any(r["event"] == "test.event" for r in rows)
    svc.close()


@pytest.mark.skipif(not _try_import_duckdb(), reason="duckdb not installed")
def test_log_query_by_session(tmp_path):
    from backend.infrastructure.log_engine.service import LogEngineService
    svc = LogEngineService(tmp_path / "logs.duckdb")
    svc.log("DEBUG", "session.start", session_id="abc")
    svc.log("DEBUG", "other", session_id="xyz")
    rows = svc.query(session_id="abc", limit=10)
    assert len(rows) == 1
    assert rows[0]["session_id"] == "abc"
    svc.close()
