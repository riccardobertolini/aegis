"""Workflow and Rule domain entities."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from .base import BaseEntity


class WorkflowStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


@dataclass
class WorkflowStep:
    step_id: str = ""
    name: str = ""
    engine: str = ""  # e.g. "inference", "knowledge"
    config: dict[str, Any] = field(default_factory=dict)
    next_step_id: str | None = None


@dataclass
class Workflow(BaseEntity):
    name: str = ""
    description: str = ""
    owner_id: str = ""
    status: WorkflowStatus = WorkflowStatus.DRAFT
    steps: list[WorkflowStep] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        super().__init__()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "owner_id": self.owner_id,
            "status": self.status.value,
            "steps": [
                {
                    "step_id": s.step_id,
                    "name": s.name,
                    "engine": s.engine,
                    "config": s.config,
                    "next_step_id": s.next_step_id,
                }
                for s in self.steps
            ],
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class Rule(BaseEntity):
    name: str = ""
    description: str = ""
    resource: str = ""
    condition: dict[str, Any] = field(default_factory=dict)  # JSON-serialisable expression
    action: str = ""
    priority: int = 0
    is_active: bool = True
    owner_id: str = ""

    def __post_init__(self) -> None:
        super().__init__()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "resource": self.resource,
            "condition": self.condition,
            "action": self.action,
            "priority": self.priority,
            "is_active": self.is_active,
            "owner_id": self.owner_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
