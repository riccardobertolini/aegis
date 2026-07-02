"""SQLModel tables for memory engine."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class ConversationTurnRecord(SQLModel, table=True):
    __tablename__ = "conversation_turns"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(index=True)
    role: str  # user | assistant | system
    content: str
    intent: Optional[str] = None
    metadata_json: str = Field(default="{}")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SessionSummaryRecord(SQLModel, table=True):
    __tablename__ = "session_summaries"

    session_id: str = Field(primary_key=True)
    summary: str
    turn_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
