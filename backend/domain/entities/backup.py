"""Backup domain entity."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .base import BaseEntity


class BackupStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Backup(BaseEntity):
    label: str = ""
    storage_path: str = ""     # path to encrypted archive
    checksum_sha256: str = ""
    size_bytes: int = 0
    status: BackupStatus = BackupStatus.PENDING
    includes: list[str] = field(default_factory=list)  # "db", "documents", "models"
    initiated_by: str = ""
    error_message: str | None = None

    def __post_init__(self) -> None:
        super().__init__()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "storage_path": self.storage_path,
            "checksum_sha256": self.checksum_sha256,
            "size_bytes": self.size_bytes,
            "status": self.status.value,
            "includes": self.includes,
            "initiated_by": self.initiated_by,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
