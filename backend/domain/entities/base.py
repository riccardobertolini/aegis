"""Base entity with common fields."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any


def _utcnow() -> datetime:
    return datetime.now(tz=UTC)


class BaseEntity:
    """All domain entities inherit from this."""

    def __init__(self, id: str | None = None) -> None:
        self.id: str = id or str(uuid.uuid4())
        self.created_at: datetime = _utcnow()
        self.updated_at: datetime = _utcnow()

    def touch(self) -> None:
        self.updated_at = _utcnow()

    def to_dict(self) -> dict[str, Any]:
        raise NotImplementedError
