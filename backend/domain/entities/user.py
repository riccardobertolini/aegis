"""User, Role, Permission domain entities."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .base import BaseEntity


@dataclass
class Permission(BaseEntity):
    name: str = ""
    description: str = ""
    resource: str = ""  # e.g. "document", "model"
    action: str = ""   # e.g. "read", "write", "delete"

    def __post_init__(self) -> None:
        super().__init__()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "resource": self.resource,
            "action": self.action,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class Role(BaseEntity):
    name: str = ""
    description: str = ""
    permissions: list[str] = field(default_factory=list)  # Permission IDs

    def __post_init__(self) -> None:
        super().__init__()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "permissions": self.permissions,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class User(BaseEntity):
    username: str = ""
    email: str = ""
    hashed_password: str = ""
    role_ids: list[str] = field(default_factory=list)
    is_active: bool = True
    is_superadmin: bool = False
    last_login_at: str | None = None

    def __post_init__(self) -> None:
        super().__init__()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "hashed_password": self.hashed_password,
            "role_ids": self.role_ids,
            "is_active": self.is_active,
            "is_superadmin": self.is_superadmin,
            "last_login_at": self.last_login_at,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
