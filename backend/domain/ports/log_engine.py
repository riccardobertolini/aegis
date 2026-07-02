"""Port: Log Engine."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class LogEntry:
    timestamp: datetime
    level: str
    message: str
    source: str
    context: dict = field(default_factory=dict)


@dataclass
class LogQuery:
    level: str | None = None
    source: str | None = None
    since: datetime | None = None
    until: datetime | None = None
    limit: int = 100


class ILogEnginePort(ABC):
    """Contract for log query interface (read side)."""

    @abstractmethod
    async def query(self, q: LogQuery) -> list[LogEntry]: ...

    @abstractmethod
    async def tail(self, n: int = 50) -> list[LogEntry]: ...
