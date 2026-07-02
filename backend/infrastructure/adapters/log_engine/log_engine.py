"""LogEngine — DuckDB-backed structured log store + analysis.

Implements ILogEnginePort.
Features:
- Structured log ingestion (from file or direct ingest).
- DuckDB columnar store for fast analytical queries.
- Pattern detection via regex rules.
- Severity histogram and top-N sources.
- The system's own structlog sink writes to this engine via
  ``AegisLogSink`` (see shared/logging.py integration below).
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

import duckdb

from backend.domain.ports.log_engine import ILogEnginePort, LogEntry, LogQuery
from backend.shared.config import Settings, get_settings
from backend.shared.logging import get_logger

logger = get_logger(__name__)

_DDL = """
CREATE TABLE IF NOT EXISTS log_entries (
    id        BIGINT DEFAULT nextval('log_seq'),
    ts        TIMESTAMP NOT NULL,
    level     VARCHAR  NOT NULL,
    source    VARCHAR  NOT NULL,
    message   TEXT     NOT NULL,
    context   VARCHAR  DEFAULT '{}'
);
CREATE SEQUENCE IF NOT EXISTS log_seq;
CREATE INDEX IF NOT EXISTS idx_log_ts     ON log_entries (ts);
CREATE INDEX IF NOT EXISTS idx_log_level  ON log_entries (level);
CREATE INDEX IF NOT EXISTS idx_log_source ON log_entries (source);
"""

# Built-in pattern rules — extend via config or Admin Studio
_PATTERN_RULES: list[dict] = [
    {
        "name": "OutOfMemory",
        "pattern": re.compile(r"out of memory|oom|cannot allocate", re.IGNORECASE),
        "severity": "CRITICAL",
    },
    {
        "name": "ConnectionRefused",
        "pattern": re.compile(r"connection refused|connect timeout", re.IGNORECASE),
        "severity": "ERROR",
    },
    {
        "name": "Traceback",
        "pattern": re.compile(r"Traceback \(most recent call last\)", re.IGNORECASE),
        "severity": "ERROR",
    },
    {
        "name": "SlowQuery",
        "pattern": re.compile(r"slow query|query took \d+ms", re.IGNORECASE),
        "severity": "WARNING",
    },
    {
        "name": "AuthFailure",
        "pattern": re.compile(r"auth.*fail|invalid token|unauthorized", re.IGNORECASE),
        "severity": "WARNING",
    },
]


class LogEngine(ILogEnginePort):
    """DuckDB-backed log engine."""

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
                        pass
        return self._conn

    # ------------------------------------------------------------------
    # ILogEnginePort
    # ------------------------------------------------------------------

    async def query(self, q: LogQuery) -> list[LogEntry]:
        conditions = ["1=1"]
        params: list = []

        if q.level:
            conditions.append("level = ?")
            params.append(q.level.upper())
        if q.source:
            conditions.append("source LIKE ?")
            params.append(f"%{q.source}%")
        if q.since:
            conditions.append("ts >= ?")
            params.append(q.since)
        if q.until:
            conditions.append("ts <= ?")
            params.append(q.until)

        where = " AND ".join(conditions)
        sql = f"""
            SELECT ts, level, message, source, context
            FROM log_entries
            WHERE {where}
            ORDER BY ts DESC
            LIMIT ?
        """
        params.append(q.limit)
        rows = self._db().execute(sql, params).fetchall()
        return [
            LogEntry(
                timestamp=row[0],
                level=row[1],
                message=row[2],
                source=row[3],
                context=json.loads(row[4]) if row[4] else {},
            )
            for row in rows
        ]

    async def tail(self, n: int = 50) -> list[LogEntry]:
        rows = self._db().execute(
            "SELECT ts, level, message, source, context "
            "FROM log_entries ORDER BY ts DESC LIMIT ?",
            [n],
        ).fetchall()
        return [
            LogEntry(
                timestamp=row[0],
                level=row[1],
                message=row[2],
                source=row[3],
                context=json.loads(row[4]) if row[4] else {},
            )
            for row in reversed(rows)  # chronological order
        ]

    # ------------------------------------------------------------------
    # Ingestion (beyond Port contract)
    # ------------------------------------------------------------------

    async def ingest(self, entry: LogEntry) -> None:
        """Write a LogEntry directly (used by AegisLogSink)."""
        self._db().execute(
            "INSERT INTO log_entries (ts, level, source, message, context) "
            "VALUES (?, ?, ?, ?, ?)",
            [
                entry.timestamp,
                entry.level.upper(),
                entry.source,
                entry.message,
                json.dumps(entry.context),
            ],
        )
        logger.debug("log_engine.ingest", level=entry.level, source=entry.source)

    async def ingest_file(
        self,
        path: Path,
        source_name: str | None = None,
        fmt: str = "jsonl",
    ) -> int:
        """Bulk-ingest a log file. Returns number of entries ingested."""
        count = 0
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    if fmt == "jsonl":
                        d = json.loads(line)
                        entry = LogEntry(
                            timestamp=datetime.fromisoformat(
                                d.get("timestamp", d.get("ts", datetime.utcnow().isoformat()))
                            ),
                            level=d.get("level", "INFO").upper(),
                            message=d.get("message", d.get("msg", line)),
                            source=source_name or d.get("source", "external"),
                            context={k: v for k, v in d.items()
                                     if k not in {"timestamp", "ts", "level", "message", "msg", "source"}},
                        )
                    else:  # plain text
                        entry = LogEntry(
                            timestamp=datetime.utcnow(),
                            level="INFO",
                            message=line,
                            source=source_name or path.name,
                        )
                    await self.ingest(entry)
                    count += 1
                except Exception as exc:
                    logger.warning("log_engine.ingest_line_error", error=str(exc))
        logger.info("log_engine.ingest_file", path=str(path), count=count)
        return count

    # ------------------------------------------------------------------
    # Analytics (beyond Port contract)
    # ------------------------------------------------------------------

    async def severity_histogram(self) -> dict[str, int]:
        rows = self._db().execute(
            "SELECT level, COUNT(*) FROM log_entries GROUP BY level ORDER BY level"
        ).fetchall()
        return {r[0]: r[1] for r in rows}

    async def top_sources(self, n: int = 10) -> list[tuple[str, int]]:
        rows = self._db().execute(
            "SELECT source, COUNT(*) as cnt FROM log_entries "
            "GROUP BY source ORDER BY cnt DESC LIMIT ?",
            [n],
        ).fetchall()
        return [(r[0], r[1]) for r in rows]

    async def detect_patterns(
        self, entries: list[LogEntry] | None = None
    ) -> list[dict]:
        """Run built-in regex patterns against recent entries.
        If entries is None, uses last 500 rows.
        """
        if entries is None:
            entries = await self.tail(500)

        hits: list[dict] = []
        for rule in _PATTERN_RULES:
            matched = [
                e for e in entries
                if rule["pattern"].search(e.message)
            ]
            if matched:
                hits.append({
                    "pattern": rule["name"],
                    "severity": rule["severity"],
                    "count": len(matched),
                    "first_seen": matched[0].timestamp.isoformat(),
                    "last_seen": matched[-1].timestamp.isoformat(),
                    "sample": matched[-1].message[:200],
                })
        return hits
