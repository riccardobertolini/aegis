"""SQLite repository for User entities."""
from __future__ import annotations

from typing import List, Optional

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.domain.models import User
from backend.infrastructure.adapters.repositories.base_sqlite import BaseSQLiteRepository


class UserRepository(BaseSQLiteRepository[User]):
    model = User

    async def find_by_username(self, username: str, session: AsyncSession) -> Optional[User]:
        result = await session.exec(select(User).where(User.username == username))
        return result.first()

    async def find_by_email(self, email: str, session: AsyncSession) -> Optional[User]:
        result = await session.exec(select(User).where(User.email == email))
        return result.first()

    async def find_active(self, session: AsyncSession) -> List[User]:
        result = await session.exec(select(User).where(User.is_active == True))  # noqa: E712
        return list(result.all())
