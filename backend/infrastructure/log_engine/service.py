"""LogEngineService — structured append-only logs on DuckDB."""
from __future__ import annotations

import json
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class LogEngineService:
    """
    Append-only columnar log store using DuckDB (embedded, local file).
    Implements ILogEnginePort contract.
    Thread-safe via a single per-instance lock.
    """

    _CREATE_SQL = """
    CREATE TABLE IF NOT EXISTS application_logs (
        id         BIGINT PRIMARY KEY,
        timestamp  TIMESTAMPTZ NOT NULL,
        level      VARCHAR(16) NOT NULL,
        component  VARCHAR(128),
        session_id VARCHAR(128),
        user_id    VARCHAR(128),
        event      VARCHAR(256),
        payload    JSON,
        trace_id   VARCHAR(64)
    );
    CREATE SEQUENCE IF NOT EXISTS log_id_seq START 1;
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

    def log(
        self,
        level: str,
        event: str,
        component: str | None = None,
        session_id: str | None = None,
        user_id: str | None = None,
        payload: dict | None = None,
        trace_id: str | None = None,
    ) -> None:
        with self._lock:
            self._connect()
            self._conn.execute(
                """
                INSERT INTO application_logs
                    (id, timestamp, level, component, session_id, user_id, event, payload, trace_id)
                VALUES (nextval('log_id_seq'), ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    datetime.now(UTC),
                    level.upper(),
                    component,
                    session_id,
                    user_id,
                    event,
                    json.dumps(payload or {}),
                    trace_id,
                ],
            )

    def query(
        self,
        level: str | None = None,
        component: str | None = None,
        session_id: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        with self._lock:
            self._connect()
            clauses = []
            params: list[Any] = []
            if level:
                clauses.append("level = ?")
                params.append(level.upper())
            if component:
                clauses.append("component = ?")
                params.append(component)
            if session_id:
                clauses.append("session_id = ?")
                params.append(session_id)
            if since:
                clauses.append("timestamp >= ?")
                params.append(since)
            if until:
                clauses.append("timestamp <= ?")
                params.append(until)
            where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
            sql = f"SELECT * FROM application_logs {where} ORDER BY timestamp DESC LIMIT {limit}"
            self._conn.execute(sql, params).fetchall()
            cols = [d[0] for d in self._conn.execute(sql, params).description]
            # re-execute to get description + data together
            result = self._conn.execute(sql, params)
            cols = [d[0] for d in result.description]
            return [dict(zip(cols, row)) for row in result.fetchall()]

    def close(self) -> None:
        with self._lock:
            if self._conn:
                self._conn.close()
                self._conn = None
