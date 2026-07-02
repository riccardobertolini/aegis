"""Audit log domain entity."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .base import BaseEntity


@dataclass
class AuditLog(BaseEntity):
    actor_id: str = ""
    actor_username: str = ""
    action: str = ""           # e.g. "document.upload"
    resource_type: str = ""    # e.g. "document"
    resource_id: str = ""
    outcome: str = "ok"        # "ok" | "error"
    ip_address: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        super().__init__()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "actor_id": self.actor_id,
            "actor_username": self.actor_username,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "outcome": self.outcome,
            "ip_address": self.ip_address,
            "details": self.details,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
