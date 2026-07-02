"""Memory / session domain entities."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .base import BaseEntity


@dataclass
class MemoryEntry(BaseEntity):
    session_id: str = ""
    assistant_id: str = ""
    user_id: str = ""
    role: str = "user"  # "user" | "assistant" | "system"
    content: str = ""
    embedding_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    is_encrypted: bool = False

    def __post_init__(self) -> None:
        super().__init__()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "assistant_id": self.assistant_id,
            "user_id": self.user_id,
            "role": self.role,
            "content": self.content,
            "embedding_id": self.embedding_id,
            "metadata": self.metadata,
            "is_encrypted": self.is_encrypted,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
