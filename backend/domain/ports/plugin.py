"""Port: Plugin Engine."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class PluginStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    PENDING = "pending"


@dataclass
class PluginManifest:
    plugin_id: str
    name: str
    version: str
    description: str
    author: str = ""
    permissions: list[str] = field(default_factory=list)  # allowed: ["fs_read", "db_read"]
    entry_point: str = "main.py"                          # relative path inside plugin dir
    signature: str | None = None                       # HMAC-SHA256 of manifest JSON
    checksum: str | None = None                        # SHA-256 of entry_point file
    installed_at: datetime | None = None
    status: PluginStatus = PluginStatus.INACTIVE


@dataclass
class PluginCallResult:
    plugin_id: str
    method: str
    result: dict
    elapsed_ms: float
    error: str | None = None


# Allowed permission tokens
ALLOWED_PERMISSIONS: frozenset[str] = frozenset({
    "fs_read",    # read files under plugin's own data dir
    "db_read",    # read from local SQLite (read-only)
    "memory_read",# read conversation memory
    "inference",  # call the local inference engine
})

# Permissions that are NEVER grantable
DENIED_PERMISSIONS: frozenset[str] = frozenset({
    "network",
    "fs_write_global",
    "exec",
    "shell",
})


class IPluginPort(ABC):
    """Contract for sandboxed plugin lifecycle."""

    @abstractmethod
    async def install(self, plugin_dir: str) -> PluginManifest: ...

    @abstractmethod
    async def uninstall(self, plugin_id: str) -> None: ...

    @abstractmethod
    async def load(self, plugin_id: str) -> PluginManifest: ...

    @abstractmethod
    async def unload(self, plugin_id: str) -> None: ...

    @abstractmethod
    async def enable(self, plugin_id: str) -> None: ...

    @abstractmethod
    async def disable(self, plugin_id: str) -> None: ...

    @abstractmethod
    async def call(self, plugin_id: str, method: str, payload: dict) -> PluginCallResult: ...

    @abstractmethod
    async def list_plugins(self) -> list[PluginManifest]: ...

    @abstractmethod
    async def get_manifest(self, plugin_id: str) -> PluginManifest | None: ...

    @abstractmethod
    async def verify_integrity(self, plugin_id: str) -> bool: ...
