"""SQLite repository for KnowledgeBase and Category entities."""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.domain.models import Category, KnowledgeBase
from backend.infrastructure.adapters.repositories.base_sqlite import BaseSQLiteRepository


class KnowledgeBaseRepository(BaseSQLiteRepository[KnowledgeBase]):
    """Concrete repository for KnowledgeBase."""

    model = KnowledgeBase

    async def find_by_assistant(self, assistant_id: UUID, session: AsyncSession) -> List[KnowledgeBase]:
        result = await session.exec(
            select(KnowledgeBase).where(KnowledgeBase.assistant_id == assistant_id)
        )
        return list(result.all())

    async def find_by_name(self, name: str, session: AsyncSession) -> Optional[KnowledgeBase]:
        result = await session.exec(
            select(KnowledgeBase).where(KnowledgeBase.name == name)
        )
        return result.first()


class CategoryRepository(BaseSQLiteRepository[Category]):
    """Concrete repository for Category."""

    model = Category

    async def find_by_knowledge_base(
        self, knowledge_base_id: UUID, session: AsyncSession
    ) -> List[Category]:
        result = await session.exec(
            select(Category).where(Category.knowledge_base_id == knowledge_base_id)
        )
        return list(result.all())

    async def find_by_parent(
        self, parent_id: Optional[UUID], session: AsyncSession
    ) -> List[Category]:
        result = await session.exec(
            select(Category).where(Category.parent_id == parent_id)
        )
        return list(result.all())
