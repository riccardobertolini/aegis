"""Port: Administration Engine."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class SystemHealth:
    status: str  # "healthy" | "degraded" | "unhealthy"
    components: dict = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


@dataclass
class BackupConfig:
    destination_path: str
    include_models: bool = False
    compress: bool = True


class IAdministrationPort(ABC):
    """Contract for system administration operations."""

    @abstractmethod
    async def health_check(self) -> SystemHealth: ...

    @abstractmethod
    async def backup(self, config: BackupConfig) -> str:
        """Create a backup. Returns path to backup archive."""
        ...

    @abstractmethod
    async def restore(self, backup_path: str) -> None: ...

    @abstractmethod
    async def list_users(self) -> list[dict]: ...

    @abstractmethod
    async def create_user(self, username: str, password: str, roles: list[str]) -> dict: ...

    @abstractmethod
    async def delete_user(self, user_id: str) -> None: ...
