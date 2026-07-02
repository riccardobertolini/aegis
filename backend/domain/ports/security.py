"""Port: Security Engine."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class UserCredentials:
    username: str
    password: str


@dataclass
class AuthToken:
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class UserPrincipal:
    user_id: str
    username: str
    roles: list[str] = field(default_factory=list)


class ISecurityPort(ABC):
    """Contract for AuthN/AuthZ and secret management."""

    @abstractmethod
    async def authenticate(self, credentials: UserCredentials) -> AuthToken: ...

    @abstractmethod
    async def verify_token(self, token: str) -> UserPrincipal: ...

    @abstractmethod
    async def authorize(self, principal: UserPrincipal, resource: str, action: str) -> bool: ...

    @abstractmethod
    async def hash_password(self, password: str) -> str: ...

    @abstractmethod
    async def verify_password(self, password: str, hashed: str) -> bool: ...
