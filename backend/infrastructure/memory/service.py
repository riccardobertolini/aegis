"""MemoryService — implements IMemoryPort using SQLite (aiosqlite/SQLModel)."""
from __future__ import annotations

import json
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from backend.domain.ports.memory import (
    IMemoryPort,
    MemoryEntry,
    MemoryRole,
    SessionSummary,
)
from backend.infrastructure.memory.models import (
    ConversationTurnRecord,
    SessionSummaryRecord,
)


class MemoryService(IMemoryPort):
    """
    Short-term: last N turns stored in SQLite per session_id.
    Long-term: lightweight extractive summary stored in session_summaries table.
    Summarisation is rule-based (no inference dependency); inject IInferencePort
    for richer summaries via the optional `summariser` parameter.
    """

    def __init__(self, session: AsyncSession, summariser=None):
        self._session = session
        self._summariser = summariser  # optional: IInferencePort

    async def append(self, entry: MemoryEntry) -> None:
        record = ConversationTurnRecord(
            session_id=entry.session_id,
            role=entry.role.value if isinstance(entry.role, MemoryRole) else entry.role,
            content=entry.content,
            intent=entry.intent,
            metadata_json=json.dumps(entry.metadata),
            timestamp=entry.timestamp,
        )
        self._session.add(record)
        await self._session.commit()

    async def get_history(
        self, session_id: str, last_n: int = 20
    ) -> list[MemoryEntry]:
        stmt = (
            select(ConversationTurnRecord)
            .where(ConversationTurnRecord.session_id == session_id)
            .order_by(ConversationTurnRecord.timestamp.desc())
            .limit(last_n)
        )
        result = await self._session.execute(stmt)
        rows = list(result.scalars().all())
        rows.reverse()  # chronological order
        return [
            MemoryEntry(
                session_id=r.session_id,
                role=MemoryRole(r.role),
                content=r.content,
                intent=r.intent,
                timestamp=r.timestamp,
                metadata=json.loads(r.metadata_json or "{}"),
            )
            for r in rows
        ]

    async def clear_session(self, session_id: str) -> None:
        stmt = select(ConversationTurnRecord).where(
            ConversationTurnRecord.session_id == session_id
        )
        result = await self._session.execute(stmt)
        for row in result.scalars().all():
            await self._session.delete(row)
        await self._session.commit()

    async def summarize_session(self, session_id: str) -> str:
        history = await self.get_history(session_id, last_n=100)
        if not history:
            return ""

        if self._summariser is not None:
            try:
                from backend.domain.ports.inference import InferenceRequest
                turns = "\n".join(
                    f"{e.role}: {e.content[:200]}" for e in history[-20:]
                )
                prompt = (
                    "Summarise this conversation in 3-5 sentences:\n"
                    f"{turns}\nSummary:"
                )
                resp = await self._summariser.run(
                    InferenceRequest(prompt=prompt, model_id="", max_tokens=256, temperature=0.3)
                )
                summary = resp.text.strip()
            except Exception:
                summary = self._extractive_summary(history)
        else:
            summary = self._extractive_summary(history)

        rec = SessionSummaryRecord(
            session_id=session_id,
            summary=summary,
            turn_count=len(history),
            updated_at=datetime.now(UTC),
        )
        existing = await self._session.get(SessionSummaryRecord, session_id)
        if existing:
            existing.summary = summary
            existing.turn_count = len(history)
            existing.updated_at = rec.updated_at
            self._session.add(existing)
        else:
            self._session.add(rec)
        await self._session.commit()
        return summary

    async def list_sessions(
        self, page: int = 0, page_size: int = 20
    ) -> list[str]:
        # Distinct session IDs ordered by most recent turn
        from sqlalchemy import func
        stmt = (
            select(ConversationTurnRecord.session_id)
            .group_by(ConversationTurnRecord.session_id)
            .order_by(func.max(ConversationTurnRecord.timestamp).desc())
            .offset(page * page_size)
            .limit(page_size)
        )
        result = await self._session.execute(stmt)
        return [row[0] for row in result.all()]

    async def get_summary(self, session_id: str) -> SessionSummary | None:
        rec = await self._session.get(SessionSummaryRecord, session_id)
        if not rec:
            return None
        return SessionSummary(
            session_id=rec.session_id,
            summary=rec.summary,
            turn_count=rec.turn_count,
            created_at=rec.created_at,
        )

    # ── helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _extractive_summary(history: list[MemoryEntry]) -> str:
        """Fallback: first user message + last assistant message."""
        user_msgs = [e.content for e in history if e.role == MemoryRole.USER]
        asst_msgs = [e.content for e in history if e.role == MemoryRole.ASSISTANT]
        parts = []
        if user_msgs:
            parts.append(f"User asked: {user_msgs[0][:200]}")
        if asst_msgs:
            parts.append(f"Last answer: {asst_msgs[-1][:200]}")
        parts.append(f"({len(history)} turns total)")
        return " | ".join(parts)
