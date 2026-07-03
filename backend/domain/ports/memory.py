"""Port: Memory Engine (conversation / session state)."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class MemoryRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class MemoryEntry:
    session_id: str
    role: MemoryRole
    content: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict = field(default_factory=dict)
    intent: str | None = None


@dataclass
class SessionSummary:
    session_id: str
    summary: str
    turn_count: int
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class IMemoryPort(ABC):
    """Contract for short/long-term conversation memory."""

    @abstractmethod
    async def append(self, entry: MemoryEntry) -> None: ...

    @abstractmethod
    async def get_history(self, session_id: str, last_n: int = 20) -> list[MemoryEntry]: ...

    @abstractmethod
    async def clear_session(self, session_id: str) -> None: ...

    @abstractmethod
    async def summarize_session(self, session_id: str) -> str: ...

    @abstractmethod
    async def list_sessions(self, page: int = 0, page_size: int = 20) -> list[str]: ...

    @abstractmethod
    async def get_summary(self, session_id: str) -> SessionSummary | None: ...
