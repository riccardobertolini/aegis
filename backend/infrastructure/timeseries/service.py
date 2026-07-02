"""TimeSeriesService — metric ingestion and query via DuckDB."""
from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class TimeSeriesService:
    """
    Local metric store: record numeric metrics (latency, token counts, etc.)
    in DuckDB for fast aggregation and trend analysis.
    """

    _CREATE_SQL = """
    CREATE TABLE IF NOT EXISTS metrics (
        id         BIGINT PRIMARY KEY,
        timestamp  TIMESTAMPTZ NOT NULL,
        name       VARCHAR(256) NOT NULL,
        value      DOUBLE NOT NULL,
        tags       JSON,
        unit       VARCHAR(64)
    );
    CREATE SEQUENCE IF NOT EXISTS metric_id_seq START 1;
    """

    def __init__(self, db_path: Path):
        self._path = db_path
        self._lock = threading.Lock()
        self._conn = None

    def _connect(self):
        if self._conn is not None:
            return
        try:
            import duckdb  # type: ignore
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = duckdb.connect(str(self._path))
            self._conn.execute(self._CREATE_SQL)
        except ImportError:
            raise RuntimeError("duckdb is not installed. Add it to requirements/base.txt.")

    def record(
        self,
        name: str,
        value: float,
        tags: dict | None = None,
        unit: str | None = None,
        timestamp: datetime | None = None,
    ) -> None:
        ts = timestamp or datetime.now(timezone.utc)
        with self._lock:
            self._connect()
            self._conn.execute(
                "INSERT INTO metrics (id, timestamp, name, value, tags, unit) "
                "VALUES (nextval('metric_id_seq'), ?, ?, ?, ?, ?)",
                [ts, name, float(value), json.dumps(tags or {}), unit],
            )

    def query(
        self,
        name: str,
        since: datetime | None = None,
        until: datetime | None = None,
        tags: dict | None = None,
        limit: int = 1000,
    ) -> list[dict[str, Any]]:
        with self._lock:
            self._connect()
            clauses = ["name = ?"]
            params: list[Any] = [name]
            if since:
                clauses.append("timestamp >= ?")
                params.append(since)
            if until:
                clauses.append("timestamp <= ?")
                params.append(until)
            where = "WHERE " + " AND ".join(clauses)
            sql = f"SELECT * FROM metrics {where} ORDER BY timestamp DESC LIMIT {limit}"
            result = self._conn.execute(sql, params)
            cols = [d[0] for d in result.description]
            return [dict(zip(cols, row)) for row in result.fetchall()]

    def aggregate(
        self,
        name: str,
        agg: str = "avg",  # avg | sum | min | max | count
        bucket: str = "1 hour",
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[dict[str, Any]]:
        with self._lock:
            self._connect()
            agg = agg.lower()
            if agg not in {"avg", "sum", "min", "max", "count"}:
                raise ValueError(f"Unsupported aggregation: {agg}")
            clauses = ["name = ?"]
            params: list[Any] = [name]
            if since:
                clauses.append("timestamp >= ?")
                params.append(since)
            if until:
                clauses.append("timestamp <= ?")
                params.append(until)
            where = "WHERE " + " AND ".join(clauses)
            sql = (
                f"SELECT time_bucket(INTERVAL '{bucket}', timestamp) AS bucket, "
                f"{agg}(value) AS value "
                f"FROM metrics {where} "
                f"GROUP BY bucket ORDER BY bucket DESC LIMIT 200"
            )
            result = self._conn.execute(sql, params)
            cols = [d[0] for d in result.description]
            return [dict(zip(cols, row)) for row in result.fetchall()]

    def close(self) -> None:
        with self._lock:
            if self._conn:
                self._conn.close()
                self._conn = None
