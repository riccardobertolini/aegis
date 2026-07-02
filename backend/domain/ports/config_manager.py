"""Config manager port — offline, per-assistant overrides, feature flags."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class IConfigManagerPort(ABC):
    """Port for reading/writing Aegis configuration, always local."""

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Return global config value."""

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Persist global config value."""

    @abstractmethod
    def get_assistant_override(self, assistant_id: str, key: str, default: Any = None) -> Any:
        """Return per-assistant override or fall back to global."""

    @abstractmethod
    def set_assistant_override(self, assistant_id: str, key: str, value: Any) -> None:
        """Persist per-assistant override."""

    @abstractmethod
    def delete_assistant_override(self, assistant_id: str, key: str) -> None:
        """Remove a per-assistant override (reverts to global)."""

    @abstractmethod
    def is_feature_enabled(self, flag: str, assistant_id: str | None = None) -> bool:
        """Check a feature flag, respecting per-assistant override."""

    @abstractmethod
    def set_feature_flag(self, flag: str, enabled: bool, assistant_id: str | None = None) -> None:
        """Enable/disable a feature flag globally or per-assistant."""

    @abstractmethod
    def export_config(self, path: str) -> None:
        """Export full config to an encrypted JSON file at `path`."""

    @abstractmethod
    def import_config(self, path: str) -> None:
        """Import config from an encrypted JSON file at `path`."""
