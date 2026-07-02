"""Assistant domain entity."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .base import BaseEntity


@dataclass
class AssistantConfig:
    """Per-assistant configuration overrides."""
    model_id: str = ""
    system_prompt: str = ""
    temperature: float = 0.7
    max_tokens: int = 2048
    feature_flags: dict[str, bool] = field(default_factory=dict)
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class Assistant(BaseEntity):
    name: str = ""
    description: str = ""
    owner_id: str = ""
    config: AssistantConfig = field(default_factory=AssistantConfig)
    is_active: bool = True
    version: int = 1
    knowledge_base_ids: list[str] = field(default_factory=list)
    plugin_ids: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        super().__init__()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "owner_id": self.owner_id,
            "config": {
                "model_id": self.config.model_id,
                "system_prompt": self.config.system_prompt,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
                "feature_flags": self.config.feature_flags,
                "extra": self.config.extra,
            },
            "is_active": self.is_active,
            "version": self.version,
            "knowledge_base_ids": self.knowledge_base_ids,
            "plugin_ids": self.plugin_ids,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
