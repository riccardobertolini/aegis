"""SQLModel tables for memory engine."""
from __future__ import annotations

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class ConversationTurnRecord(SQLModel, table=True):
    __tablename__ = "conversation_turns"

    id: int | None = Field(default=None, primary_key=True)
    session_id: str = Field(index=True)
    role: str  # user | assistant | system
    content: str
    intent: str | None = None
    metadata_json: str = Field(default="{}")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SessionSummaryRecord(SQLModel, table=True):
    __tablename__ = "session_summaries"

    session_id: str = Field(primary_key=True)
    summary: str
    turn_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
