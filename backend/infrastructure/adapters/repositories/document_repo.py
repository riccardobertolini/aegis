"""SQLite repositories for Document, Category, KnowledgeBase entities."""
from __future__ import annotations

from sqlmodel import select

from backend.infrastructure.adapters.repositories.base_sqlite import BaseSQLiteRepository
from backend.infrastructure.database.models import (
    CategoryModel,
    DocumentModel,
    KnowledgeBaseModel,
)


class SQLiteDocumentRepository(BaseSQLiteRepository[DocumentModel]):
    model = DocumentModel

    async def find_by_owner(self, owner_id: str) -> list[DocumentModel]:
        result = await self._session.exec(
            select(DocumentModel).where(DocumentModel.owner_id == owner_id)
        )
        return list(result.all())

    async def find_by_status(self, status: str) -> list[DocumentModel]:
        result = await self._session.exec(
            select(DocumentModel).where(DocumentModel.status == status)
        )
        return list(result.all())

    async def find_by_checksum(self, checksum: str) -> DocumentModel | None:
        result = await self._session.exec(
            select(DocumentModel).where(DocumentModel.checksum_sha256 == checksum)
        )
        return result.first()


DocumentRepository = SQLiteDocumentRepository


class SQLiteCategoryRepository(BaseSQLiteRepository[CategoryModel]):
    model = CategoryModel

    async def find_by_name(self, name: str) -> CategoryModel | None:
        result = await self._session.exec(
            select(CategoryModel).where(CategoryModel.name == name)
        )
        return result.first()

    async def find_children(self, parent_id: str) -> list[CategoryModel]:
        result = await self._session.exec(
            select(CategoryModel).where(CategoryModel.parent_id == parent_id)
        )
        return list(result.all())

    async def find_roots(self) -> list[CategoryModel]:
        result = await self._session.exec(
            select(CategoryModel).where(CategoryModel.parent_id == None)  # noqa: E711
        )
        return list(result.all())


CategoryRepository = SQLiteCategoryRepository


class SQLiteKnowledgeBaseRepository(BaseSQLiteRepository[KnowledgeBaseModel]):
    model = KnowledgeBaseModel

    async def find_by_owner(self, owner_id: str) -> list[KnowledgeBaseModel]:
        result = await self._session.exec(
            select(KnowledgeBaseModel).where(KnowledgeBaseModel.owner_id == owner_id)
        )
        return list(result.all())

    async def find_active(self) -> list[KnowledgeBaseModel]:
        result = await self._session.exec(
            select(KnowledgeBaseModel).where(KnowledgeBaseModel.is_active == True)  # noqa: E712
        )
        return list(result.all())

    async def find_by_name(self, name: str) -> KnowledgeBaseModel | None:
        result = await self._session.exec(
            select(KnowledgeBaseModel).where(KnowledgeBaseModel.name == name)
        )
        return result.first()


KnowledgeBaseRepository = SQLiteKnowledgeBaseRepository
