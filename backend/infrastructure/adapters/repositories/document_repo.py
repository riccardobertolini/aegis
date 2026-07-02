"""SQLite repository for Document entities."""
from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from backend.domain.models import Document
from backend.infrastructure.adapters.repositories.base_sqlite import BaseSQLiteRepository


class DocumentRepository(BaseSQLiteRepository[Document]):
    model = Document

    async def find_by_sha256(self, sha256: str, session: AsyncSession) -> Optional[Document]:
        result = await session.exec(select(Document).where(Document.sha256 == sha256))
        return result.first()

    async def find_by_knowledge_base(
        self, knowledge_base_id: UUID, session: AsyncSession
    ) -> List[Document]:
        result = await session.exec(
            select(Document).where(Document.knowledge_base_id == str(knowledge_base_id))
        )
        return list(result.all())

    async def find_by_category(
        self, category_id: UUID, session: AsyncSession
    ) -> List[Document]:
        result = await session.exec(
            select(Document).where(Document.category_id == str(category_id))
        )
        return list(result.all())

    async def find_encrypted(self, session: AsyncSession) -> List[Document]:
        result = await session.exec(select(Document).where(Document.is_encrypted == True))  # noqa: E712
        return list(result.all())
