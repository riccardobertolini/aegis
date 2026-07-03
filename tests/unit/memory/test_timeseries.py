"""Unit tests — TimeSeriesService (in-memory DuckDB)."""

import pytest


def _try_import_duckdb():
    try:
        import duckdb
        return True
    except ImportError:
        return False


@pytest.mark.skipif(not _try_import_duckdb(), reason="duckdb not installed")
def test_record_and_query(tmp_path):
    from backend.infrastructure.timeseries.service import TimeSeriesService
    svc = TimeSeriesService(tmp_path / "metrics.duckdb")
    svc.record("inference.latency_ms", 142.5, tags={"model": "mamba"})
    svc.record("inference.latency_ms", 98.0, tags={"model": "mamba"})
    rows = svc.query("inference.latency_ms", limit=10)
    assert len(rows) == 2
    values = [r["value"] for r in rows]
    assert 142.5 in values
    svc.close()


@pytest.mark.skipif(not _try_import_duckdb(), reason="duckdb not installed")
def test_record_with_unit(tmp_path):
    from backend.infrastructure.timeseries.service import TimeSeriesService
    svc = TimeSeriesService(tmp_path / "metrics.duckdb")
    svc.record("token.count", 512, unit="tokens")
    rows = svc.query("token.count")
    assert rows[0]["unit"] == "tokens"
    svc.close()
