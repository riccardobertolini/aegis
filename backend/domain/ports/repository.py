"""Generic repository port (interface) for all domain entities."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from backend.domain.entities.base import BaseEntity

T = TypeVar("T", bound=BaseEntity)


class IRepository(ABC, Generic[T]):
    """CRUD + query port for a domain entity."""

    @abstractmethod
    async def save(self, entity: T) -> T:
        """Insert or update an entity."""

    @abstractmethod
    async def get_by_id(self, entity_id: str) -> T | None:
        """Return entity or None."""

    @abstractmethod
    async def list_all(self, limit: int = 100, offset: int = 0) -> list[T]:
        """Return paginated list."""

    @abstractmethod
    async def delete(self, entity_id: str) -> bool:
        """Delete entity; return True if found and deleted."""

    @abstractmethod
    async def count(self) -> int:
        """Return total count."""


# --- Typed specialisations (one per aggregate) ---

class IUserRepository(IRepository):
    @abstractmethod
    async def get_by_username(self, username: str): ...
    @abstractmethod
    async def get_by_email(self, email: str): ...


class IRoleRepository(IRepository):
    @abstractmethod
    async def get_by_name(self, name: str): ...


class IPermissionRepository(IRepository):
    @abstractmethod
    async def list_by_resource(self, resource: str) -> list: ...


class IAssistantRepository(IRepository):
    @abstractmethod
    async def list_by_owner(self, owner_id: str) -> list: ...
    @abstractmethod
    async def get_active(self) -> list: ...


class IDocumentRepository(IRepository):
    @abstractmethod
    async def get_by_checksum(self, checksum: str): ...
    @abstractmethod
    async def list_by_owner(self, owner_id: str) -> list: ...
    @abstractmethod
    async def list_by_knowledge_base(self, kb_id: str) -> list: ...


class IKnowledgeBaseRepository(IRepository):
    @abstractmethod
    async def get_by_name(self, name: str): ...
    @abstractmethod
    async def list_active(self) -> list: ...


class ICategoryRepository(IRepository):
    @abstractmethod
    async def list_children(self, parent_id: str | None) -> list: ...


class IMemoryEntryRepository(IRepository):
    @abstractmethod
    async def list_by_session(self, session_id: str) -> list: ...
    @abstractmethod
    async def delete_by_session(self, session_id: str) -> int: ...


class IModelRecordRepository(IRepository):
    @abstractmethod
    async def get_by_name(self, name: str): ...
    @abstractmethod
    async def list_available(self) -> list: ...


class IDatasetRepository(IRepository):
    @abstractmethod
    async def list_by_owner(self, owner_id: str) -> list: ...


class IWorkflowRepository(IRepository):
    @abstractmethod
    async def list_by_owner(self, owner_id: str) -> list: ...
    @abstractmethod
    async def list_active(self) -> list: ...


class IRuleRepository(IRepository):
    @abstractmethod
    async def list_by_resource(self, resource: str) -> list: ...
    @abstractmethod
    async def list_active_ordered(self) -> list: ...


class IAuditLogRepository(IRepository):
    @abstractmethod
    async def list_by_actor(self, actor_id: str, limit: int = 50) -> list: ...
    @abstractmethod
    async def list_by_resource(self, resource_type: str, resource_id: str) -> list: ...


class IBackupRepository(IRepository):
    @abstractmethod
    async def list_completed(self) -> list: ...
    @abstractmethod
    async def get_latest(self): ...
