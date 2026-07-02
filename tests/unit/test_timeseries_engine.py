"""Unit tests — TimeSeriesEngine."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from backend.domain.ports.timeseries import Metric, MetricQuery, MetricSeries
from backend.infrastructure.adapters.timeseries.timeseries_engine import TimeSeriesEngine


@pytest.fixture
def tmp_settings(tmp_path):
    from backend.shared.config import Settings
    s = MagicMock(spec=Settings)
    s.duckdb_path = tmp_path / "test_ts.duckdb"
    return s


@pytest.fixture
def engine(tmp_settings):
    return TimeSeriesEngine(settings=tmp_settings)


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


class TestTimeSeriesEngine:
    def _sample_metrics(self, engine, name="cpu", n=10):
        now = datetime(2025, 1, 1, 12, 0, 0)
        for i in range(n):
            m = Metric(
                name=name,
                value=float(i * 10),
                timestamp=now + timedelta(seconds=i * 60),
            )
            run(engine.record(m))
        return now, now + timedelta(seconds=(n - 1) * 60)

    def test_record_and_query(self, engine):
        since, until = self._sample_metrics(engine, "cpu", 5)
        q = MetricQuery(name="cpu", since=since, until=until, aggregation="avg", bucket_seconds=60)
        series = run(engine.query(q))
        assert series.name == "cpu"
        assert len(series.points) >= 1

    def test_list_metrics(self, engine):
        self._sample_metrics(engine, "mem", 3)
        metrics = run(engine.list_metrics())
        assert "mem" in metrics

    def test_trend_slope_positive(self, engine):
        now = datetime(2025, 1, 1)
        points = [(now + timedelta(seconds=i * 60), float(i)) for i in range(10)]
        series = MetricSeries(name="test", points=points)
        slope = run(engine.trend_slope(series))
        assert slope > 0

    def test_trend_slope_flat(self, engine):
        now = datetime(2025, 1, 1)
        points = [(now + timedelta(seconds=i * 60), 5.0) for i in range(10)]
        series = MetricSeries(name="test", points=points)
        slope = run(engine.trend_slope(series))
        assert abs(slope) < 1e-6

    def test_anomaly_detection(self, engine):
        now = datetime(2025, 1, 1)
        normal = [(now + timedelta(seconds=i * 60), 10.0) for i in range(10)]
        spike = (now + timedelta(seconds=10 * 60), 10000.0)  # massive spike
        points = normal + [spike]
        series = MetricSeries(name="test", points=points)
        anomalies = run(engine.detect_anomalies(series, z_threshold=2.0))
        assert len(anomalies) >= 1
        assert anomalies[0][2] > 2.0  # z_score

    def test_no_anomaly_stable_series(self, engine):
        now = datetime(2025, 1, 1)
        points = [(now + timedelta(seconds=i * 60), 10.0 + i * 0.01) for i in range(20)]
        series = MetricSeries(name="test", points=points)
        anomalies = run(engine.detect_anomalies(series, z_threshold=2.5))
        assert len(anomalies) == 0
