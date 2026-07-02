"""TimeSeriesEngine — DuckDB-backed local metrics store.

Implements ITimeSeriesPort.
Features:
- Fast ingest via DuckDB columnar store.
- Bucket aggregation (avg/sum/min/max/count) with configurable window.
- Z-score anomaly detection (rolling std-dev).
- Linear-regression trend slope.
- No external service; all data stays in the local DuckDB file.
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta
from statistics import mean, stdev

import duckdb

from backend.domain.ports.timeseries import (
    ITimeSeriesPort,
    Metric,
    MetricQuery,
    MetricSeries,
)
from backend.shared.config import Settings, get_settings
from backend.shared.logging import get_logger

logger = get_logger(__name__)

_DDL = """
CREATE TABLE IF NOT EXISTS metrics (
    id        BIGINT DEFAULT nextval('metrics_seq'),
    name      VARCHAR NOT NULL,
    value     DOUBLE NOT NULL,
    ts        TIMESTAMP NOT NULL,
    tags      VARCHAR DEFAULT '{}'
);
CREATE SEQUENCE IF NOT EXISTS metrics_seq;
CREATE INDEX IF NOT EXISTS idx_metrics_name_ts ON metrics (name, ts);
"""

_AGG_MAP = {
    "avg": "AVG",
    "sum": "SUM",
    "min": "MIN",
    "max": "MAX",
    "count": "COUNT",
}


class TimeSeriesEngine(ITimeSeriesPort):
    """DuckDB-backed time series engine."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._db_path = str(self._settings.duckdb_path)
        self._conn: duckdb.DuckDBPyConnection | None = None

    def _db(self) -> duckdb.DuckDBPyConnection:
        if self._conn is None or self._conn.is_connection_closed():
            self._conn = duckdb.connect(self._db_path)
            for stmt in _DDL.strip().split(";"):
                s = stmt.strip()
                if s:
                    try:
                        self._conn.execute(s)
                    except duckdb.CatalogException:
                        pass  # sequence/table already exists
        return self._conn

    # ------------------------------------------------------------------
    # ITimeSeriesPort
    # ------------------------------------------------------------------

    async def record(self, metric: Metric) -> None:
        import json

        db = self._db()
        db.execute(
            "INSERT INTO metrics (name, value, ts, tags) VALUES (?, ?, ?, ?)",
            [metric.name, metric.value, metric.timestamp, json.dumps(metric.tags)],
        )
        logger.debug("timeseries.record", name=metric.name, value=metric.value)

    async def query(self, q: MetricQuery) -> MetricSeries:
        agg_fn = _AGG_MAP.get(q.aggregation.lower(), "AVG")
        bucket_interval = f"INTERVAL '{q.bucket_seconds} SECONDS'"
        sql = f"""
            SELECT
                time_bucket({bucket_interval}, ts) AS bucket,
                {agg_fn}(value)                    AS agg_value
            FROM metrics
            WHERE name = ?
              AND ts >= ?
              AND ts <= ?
            GROUP BY bucket
            ORDER BY bucket
        """
        # DuckDB uses time_bucket if timescaledb extension is loaded;
        # otherwise fall back to epoch-based truncation.
        try:
            rows = self._db().execute(sql, [q.name, q.since, q.until]).fetchall()
        except Exception:
            rows = self._fallback_query(q, agg_fn)

        points = [(row[0], float(row[1])) for row in rows]
        return MetricSeries(name=q.name, points=points)

    # ------------------------------------------------------------------
    # Extended analytics (beyond Port contract)
    # ------------------------------------------------------------------

    async def detect_anomalies(
        self, series: MetricSeries, z_threshold: float = 2.5
    ) -> list[tuple[datetime, float, float]]:
        """Return (timestamp, value, z_score) for anomalous points."""
        if len(series.points) < 4:
            return []
        values = [v for _, v in series.points]
        mu = mean(values)
        sigma = stdev(values) or 1e-9
        anomalies = []
        for ts, val in series.points:
            z = abs(val - mu) / sigma
            if z > z_threshold:
                anomalies.append((ts, val, round(z, 3)))
        return anomalies

    async def trend_slope(self, series: MetricSeries) -> float:
        """Return linear regression slope (value / second)."""
        if len(series.points) < 2:
            return 0.0
        xs = [ts.timestamp() for ts, _ in series.points]
        ys = [v for _, v in series.points]
        x_mean = mean(xs)
        y_mean = mean(ys)
        num = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
        den = sum((x - x_mean) ** 2 for x in xs) or 1e-9
        return num / den

    async def list_metrics(self) -> list[str]:
        rows = self._db().execute("SELECT DISTINCT name FROM metrics ORDER BY name").fetchall()
        return [r[0] for r in rows]

    # ------------------------------------------------------------------
    # Fallback bucket query (no time_bucket extension)
    # ------------------------------------------------------------------

    def _fallback_query(
        self, q: MetricQuery, agg_fn: str
    ) -> list[tuple[datetime, float]]:
        sql = """
            SELECT ts, value FROM metrics
            WHERE name = ? AND ts >= ? AND ts <= ?
            ORDER BY ts
        """
        raw = self._db().execute(sql, [q.name, q.since, q.until]).fetchall()
        if not raw:
            return []

        buckets: dict[datetime, list[float]] = {}
        for row in raw:
            ts: datetime = row[0]
            epoch = ts.timestamp()
            bucket_epoch = (epoch // q.bucket_seconds) * q.bucket_seconds
            bucket_ts = datetime.fromtimestamp(bucket_epoch)
            buckets.setdefault(bucket_ts, []).append(float(row[1]))

        result = []
        for bts in sorted(buckets):
            vals = buckets[bts]
            if agg_fn == "AVG":
                agg = mean(vals)
            elif agg_fn == "SUM":
                agg = sum(vals)
            elif agg_fn == "MIN":
                agg = min(vals)
            elif agg_fn == "MAX":
                agg = max(vals)
            else:
                agg = float(len(vals))
            result.append((bts, agg))
        return result
