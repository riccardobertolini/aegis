"""Port: Memory Engine (conversation / session state)."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class MemoryEntry:
    session_id: str
    role: str  # "user" | "assistant" | "system"
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict = field(default_factory=dict)


class IMemoryPort(ABC):
    """Contract for short/long-term conversation memory."""

    @abstractmethod
    async def append(self, entry: MemoryEntry) -> None: ...

    @abstractmethod
    async def get_history(self, session_id: str, last_n: int = 20) -> list[MemoryEntry]: ...

    @abstractmethod
    async def clear_session(self, session_id: str) -> None: ...

    @abstractmethod
    async def summarize_session(self, session_id: str) -> str:
        """Produce a text summary of the session for long-term storage."""
        ...
