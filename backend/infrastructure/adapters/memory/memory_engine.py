"""MemoryEngine — SQLite-backed conversation memory.

Implements IMemoryPort.
Features:
- Per-session history stored in SQLite (aiosqlite).
- Per-assistant namespace via ``assistant_id`` tag in metadata.
- Long-context windowing: keeps last N entries + a rolling summary.
- Incremental summarisation: produces an extractive summary without
  requiring a live model (rule-based sentence scoring); when a CoreAI
  adapter is injected it upgrades to abstractive summarisation.
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict
from datetime import datetime
from typing import Protocol

import aiosqlite

from backend.domain.ports.memory import IMemoryPort, MemoryEntry
from backend.shared.config import Settings, get_settings
from backend.shared.logging import get_logger

logger = get_logger(__name__)

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS memory_entries (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id  TEXT    NOT NULL,
    role        TEXT    NOT NULL,
    content     TEXT    NOT NULL,
    timestamp   TEXT    NOT NULL,
    metadata    TEXT    NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_memory_session
    ON memory_entries (session_id, id);
CREATE TABLE IF NOT EXISTS memory_summaries (
    session_id  TEXT PRIMARY KEY,
    summary     TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);
"""

_WINDOW_SIZE = 40  # max entries returned before windowing kicks in
_SUMMARY_TRIGGER = 60  # entries that trigger a new summary pass


class ICoreAIPort(Protocol):
    """Minimal protocol used only for abstractive summarisation."""

    async def complete(self, prompt: str) -> str:
        ...


class MemoryEngine(IMemoryPort):
    """Concrete memory engine."""

    def __init__(
        self,
        settings: Settings | None = None,
        core_ai: ICoreAIPort | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._db_path = str(self._settings.db_path)
        self._core_ai = core_ai  # optional — used for abstractive summary

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _ensure_schema(self, conn: aiosqlite.Connection) -> None:
        for stmt in _CREATE_TABLE.strip().split(";"):
            stmt = stmt.strip()
            if stmt:
                await conn.execute(stmt)
        await conn.commit()

    # ------------------------------------------------------------------
    # IMemoryPort
    # ------------------------------------------------------------------

    async def append(self, entry: MemoryEntry) -> None:
        async with aiosqlite.connect(self._db_path) as db:
            await self._ensure_schema(db)
            await db.execute(
                "INSERT INTO memory_entries (session_id, role, content, timestamp, metadata) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    entry.session_id,
                    entry.role,
                    entry.content,
                    entry.timestamp.isoformat(),
                    json.dumps(entry.metadata),
                ),
            )
            await db.commit()
            # trigger incremental summary if threshold crossed
            count_row = await db.execute_fetchall(
                "SELECT COUNT(*) FROM memory_entries WHERE session_id = ?",
                (entry.session_id,),
            )
            count = count_row[0][0] if count_row else 0
            if count > 0 and count % _SUMMARY_TRIGGER == 0:
                await self.summarize_session(entry.session_id)
        logger.debug("memory.append", session=entry.session_id, role=entry.role)

    async def get_history(
        self,
        session_id: str,
        last_n: int = 20,
    ) -> list[MemoryEntry]:
        async with aiosqlite.connect(self._db_path) as db:
            await self._ensure_schema(db)
            # Check if windowing applies
            total_rows = await db.execute_fetchall(
                "SELECT COUNT(*) FROM memory_entries WHERE session_id = ?",
                (session_id,),
            )
            total = total_rows[0][0] if total_rows else 0

            if total > _WINDOW_SIZE:
                # Prepend the rolling summary as a synthetic system entry
                summary_row = await db.execute_fetchall(
                    "SELECT summary, updated_at FROM memory_summaries WHERE session_id = ?",
                    (session_id,),
                )
                entries: list[MemoryEntry] = []
                if summary_row:
                    entries.append(
                        MemoryEntry(
                            session_id=session_id,
                            role="system",
                            content=f"[CONTEXT SUMMARY] {summary_row[0][0]}",
                            timestamp=datetime.fromisoformat(summary_row[0][1]),
                            metadata={"synthetic": True},
                        )
                    )
                rows = await db.execute_fetchall(
                    "SELECT role, content, timestamp, metadata "
                    "FROM memory_entries WHERE session_id = ? "
                    "ORDER BY id DESC LIMIT ?",
                    (session_id, min(last_n, _WINDOW_SIZE)),
                )
                entries += [
                    MemoryEntry(
                        session_id=session_id,
                        role=r[0],
                        content=r[1],
                        timestamp=datetime.fromisoformat(r[2]),
                        metadata=json.loads(r[3]),
                    )
                    for r in reversed(rows)
                ]
                return entries

            rows = await db.execute_fetchall(
                "SELECT role, content, timestamp, metadata "
                "FROM memory_entries WHERE session_id = ? "
                "ORDER BY id DESC LIMIT ?",
                (session_id, last_n),
            )
        return [
            MemoryEntry(
                session_id=session_id,
                role=r[0],
                content=r[1],
                timestamp=datetime.fromisoformat(r[2]),
                metadata=json.loads(r[3]),
            )
            for r in reversed(rows)
        ]

    async def clear_session(self, session_id: str) -> None:
        async with aiosqlite.connect(self._db_path) as db:
            await self._ensure_schema(db)
            await db.execute(
                "DELETE FROM memory_entries WHERE session_id = ?", (session_id,)
            )
            await db.execute(
                "DELETE FROM memory_summaries WHERE session_id = ?", (session_id,)
            )
            await db.commit()
        logger.info("memory.clear_session", session=session_id)

    async def summarize_session(self, session_id: str) -> str:
        """Produce a rolling summary of the session.

        Strategy:
        - If CoreAI is available: abstractive prompt-based.
        - Otherwise: extractive (top-N sentences by TF-IDF weight).
        """
        async with aiosqlite.connect(self._db_path) as db:
            await self._ensure_schema(db)
            rows = await db.execute_fetchall(
                "SELECT role, content FROM memory_entries WHERE session_id = ? ORDER BY id",
                (session_id,),
            )

        if not rows:
            return ""

        full_text = "\n".join(f"{r[0].upper()}: {r[1]}" for r in rows)

        if self._core_ai is not None:
            prompt = (
                "Produce a concise summary (max 200 words) of this conversation,"
                " preserving key facts and decisions:\n\n" + full_text
            )
            summary = await self._core_ai.complete(prompt)
        else:
            summary = _extractive_summary(full_text, max_sentences=8)

        async with aiosqlite.connect(self._db_path) as db:
            await self._ensure_schema(db)
            await db.execute(
                "INSERT INTO memory_summaries (session_id, summary, updated_at) "
                "VALUES (?, ?, ?) "
                "ON CONFLICT(session_id) DO UPDATE SET summary=excluded.summary, updated_at=excluded.updated_at",
                (session_id, summary, datetime.utcnow().isoformat()),
            )
            await db.commit()

        logger.info("memory.summarize_session", session=session_id, chars=len(summary))
        return summary

    # ------------------------------------------------------------------
    # Extra helpers (not in Port — exposed for Admin Studio)
    # ------------------------------------------------------------------

    async def list_sessions(self, assistant_id: str | None = None) -> list[str]:
        """Return distinct session IDs, optionally filtered by assistant."""
        async with aiosqlite.connect(self._db_path) as db:
            await self._ensure_schema(db)
            if assistant_id:
                rows = await db.execute_fetchall(
                    "SELECT DISTINCT session_id FROM memory_entries "
                    "WHERE json_extract(metadata,'$.assistant_id') = ?",
                    (assistant_id,),
                )
            else:
                rows = await db.execute_fetchall(
                    "SELECT DISTINCT session_id FROM memory_entries"
                )
        return [r[0] for r in rows]


# ---------------------------------------------------------------------------
# Extractive summariser (no external deps)
# ---------------------------------------------------------------------------

def _extractive_summary(text: str, max_sentences: int = 8) -> str:
    """Sentence-scoring via word frequency (simplified Luhn)."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    if len(sentences) <= max_sentences:
        return text

    # word frequency
    words = re.findall(r"\b\w+\b", text.lower())
    stop = {
        "the", "a", "an", "is", "it", "in", "on", "at", "to", "of", "and",
        "or", "but", "for", "with", "this", "that", "was", "are", "be",
        "user", "assistant", "system",
    }
    freq: dict[str, int] = {}
    for w in words:
        if w not in stop:
            freq[w] = freq.get(w, 0) + 1

    def score(s: str) -> float:
        ws = re.findall(r"\b\w+\b", s.lower())
        return sum(freq.get(w, 0) for w in ws if w not in stop) / max(len(ws), 1)

    scored = sorted(enumerate(sentences), key=lambda x: score(x[1]), reverse=True)
    top_idx = sorted(i for i, _ in scored[:max_sentences])
    return " ".join(sentences[i] for i in top_idx)
