"""Document, Category, KnowledgeBase domain entities."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from .base import BaseEntity


class DocumentStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    INDEXED = "indexed"
    ERROR = "error"


@dataclass
class Category(BaseEntity):
    name: str = ""
    description: str = ""
    parent_id: str | None = None

    def __post_init__(self) -> None:
        super().__init__()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "parent_id": self.parent_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class Document(BaseEntity):
    filename: str = ""
    original_filename: str = ""
    mime_type: str = ""
    size_bytes: int = 0
    checksum_sha256: str = ""
    storage_path: str = ""  # relative path under data/documents/
    status: DocumentStatus = DocumentStatus.PENDING
    owner_id: str = ""
    category_ids: list[str] = field(default_factory=list)
    knowledge_base_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    is_encrypted: bool = False

    def __post_init__(self) -> None:
        super().__init__()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "filename": self.filename,
            "original_filename": self.original_filename,
            "mime_type": self.mime_type,
            "size_bytes": self.size_bytes,
            "checksum_sha256": self.checksum_sha256,
            "storage_path": self.storage_path,
            "status": self.status.value,
            "owner_id": self.owner_id,
            "category_ids": self.category_ids,
            "knowledge_base_ids": self.knowledge_base_ids,
            "metadata": self.metadata,
            "is_encrypted": self.is_encrypted,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class KnowledgeBase(BaseEntity):
    name: str = ""
    description: str = ""
    owner_id: str = ""
    category_ids: list[str] = field(default_factory=list)
    is_active: bool = True
    chroma_collection_name: str = ""

    def __post_init__(self) -> None:
        super().__init__()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "owner_id": self.owner_id,
            "category_ids": self.category_ids,
            "is_active": self.is_active,
            "chroma_collection_name": self.chroma_collection_name,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
