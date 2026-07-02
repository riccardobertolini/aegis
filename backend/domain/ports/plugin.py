"""Port: Plugin Engine."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum


class PluginStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


@dataclass
class PluginManifest:
    plugin_id: str
    name: str
    version: str
    description: str
    permissions: list[str] = field(default_factory=list)
    entry_point: str = ""


class IPluginPort(ABC):
    """Contract for sandboxed plugin lifecycle."""

    @abstractmethod
    async def load(self, plugin_id: str) -> PluginManifest: ...

    @abstractmethod
    async def unload(self, plugin_id: str) -> None: ...

    @abstractmethod
    async def call(self, plugin_id: str, method: str, payload: dict) -> dict: ...

    @abstractmethod
    async def list_plugins(self) -> list[PluginManifest]: ...
