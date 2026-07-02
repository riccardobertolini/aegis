"""Concrete SQLite Document/Category/KnowledgeBase repositories."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.entities.document import Category, Document, KnowledgeBase
from backend.domain.ports.repository import ICategoryRepository, IDocumentRepository, IKnowledgeBaseRepository
from backend.infrastructure.database.mappers import (
    category_to_orm, document_to_orm, kb_to_orm,
    orm_to_category, orm_to_document, orm_to_kb,
)
from backend.infrastructure.database.models import CategoryModel, DocumentModel, KnowledgeBaseModel
from .base_sqlite import BaseSQLiteRepository


class SQLiteDocumentRepository(BaseSQLiteRepository[Document, DocumentModel], IDocumentRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, DocumentModel, document_to_orm, orm_to_document)

    async def get_by_checksum(self, checksum: str) -> Document | None:
        stmt = select(DocumentModel).where(DocumentModel.checksum_sha256 == checksum)
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        return orm_to_document(m) if m else None

    async def list_by_owner(self, owner_id: str) -> list[Document]:
        stmt = select(DocumentModel).where(DocumentModel.owner_id == owner_id)
        result = await self._session.execute(stmt)
        return [orm_to_document(m) for m in result.scalars().all()]

    async def list_by_knowledge_base(self, kb_id: str) -> list[Document]:
        stmt = select(DocumentModel)
        result = await self._session.execute(stmt)
        all_docs = [orm_to_document(m) for m in result.scalars().all()]
        return [d for d in all_docs if kb_id in d.knowledge_base_ids]


class SQLiteCategoryRepository(BaseSQLiteRepository[Category, CategoryModel], ICategoryRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, CategoryModel, category_to_orm, orm_to_category)

    async def list_children(self, parent_id: str | None) -> list[Category]:
        stmt = select(CategoryModel).where(CategoryModel.parent_id == parent_id)
        result = await self._session.execute(stmt)
        return [orm_to_category(m) for m in result.scalars().all()]


class SQLiteKnowledgeBaseRepository(BaseSQLiteRepository[KnowledgeBase, KnowledgeBaseModel], IKnowledgeBaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, KnowledgeBaseModel, kb_to_orm, orm_to_kb)

    async def get_by_name(self, name: str) -> KnowledgeBase | None:
        stmt = select(KnowledgeBaseModel).where(KnowledgeBaseModel.name == name)
        result = await self._session.execute(stmt)
        m = result.scalar_one_or_none()
        return orm_to_kb(m) if m else None

    async def list_active(self) -> list[KnowledgeBase]:
        stmt = select(KnowledgeBaseModel).where(KnowledgeBaseModel.is_active == True)  # noqa: E712
        result = await self._session.execute(stmt)
        return [orm_to_kb(m) for m in result.scalars().all()]
