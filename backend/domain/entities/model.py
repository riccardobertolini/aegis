"""Model registry and Dataset domain entities."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from .base import BaseEntity


class ModelType(StrEnum):
    SSM_MAMBA = "ssm_mamba"
    SSM_MINIMAL = "ssm_minimal"
    EMBEDDING = "embedding"
    OTHER = "other"


class ModelStatus(StrEnum):
    AVAILABLE = "available"
    LOADING = "loading"
    UNAVAILABLE = "unavailable"
    DEPRECATED = "deprecated"


@dataclass
class ModelRecord(BaseEntity):
    name: str = ""
    model_type: ModelType = ModelType.SSM_MAMBA
    status: ModelStatus = ModelStatus.UNAVAILABLE
    storage_path: str = ""  # relative under models/
    checksum_sha256: str = ""
    size_bytes: int = 0
    architecture: str = ""
    context_length: int = 2048
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        super().__init__()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "model_type": self.model_type.value,
            "status": self.status.value,
            "storage_path": self.storage_path,
            "checksum_sha256": self.checksum_sha256,
            "size_bytes": self.size_bytes,
            "architecture": self.architecture,
            "context_length": self.context_length,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class Dataset(BaseEntity):
    name: str = ""
    description: str = ""
    storage_path: str = ""
    format: str = "jsonl"  # jsonl | csv | parquet
    size_bytes: int = 0
    checksum_sha256: str = ""
    row_count: int = 0
    owner_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        super().__init__()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "storage_path": self.storage_path,
            "format": self.format,
            "size_bytes": self.size_bytes,
            "checksum_sha256": self.checksum_sha256,
            "row_count": self.row_count,
            "owner_id": self.owner_id,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
