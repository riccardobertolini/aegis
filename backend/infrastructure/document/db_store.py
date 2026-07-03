"""SQLite document metadata store (SQLModel + aiosqlite)."""
from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Field, SQLModel, select


class DocumentRecord(SQLModel, table=True):
    __tablename__ = "documents"

    id: str = Field(primary_key=True)
    filename: str
    mime_type: str
    status: str = "pending"
    error: str | None = None
    char_count: int = 0
    chunk_count: int = 0
    metadata_json: str = Field(default="{}")  # JSON blob
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class DocumentDBStore:
    """Async CRUD for DocumentRecord via an existing AsyncSession."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def upsert(self, record: DocumentRecord) -> None:
        record.updated_at = datetime.now(UTC)
        existing = await self._session.get(DocumentRecord, record.id)
        if existing:
            for k, v in record.model_dump(exclude={"id", "created_at"}).items():
                setattr(existing, k, v)
            self._session.add(existing)
        else:
            self._session.add(record)
        await self._session.commit()

    async def get(self, doc_id: str) -> DocumentRecord | None:
        return await self._session.get(DocumentRecord, doc_id)

    async def delete(self, doc_id: str) -> None:
        rec = await self._session.get(DocumentRecord, doc_id)
        if rec:
            await self._session.delete(rec)
            await self._session.commit()

    async def list_page(
        self, page: int = 0, page_size: int = 20
    ) -> list[DocumentRecord]:
        stmt = (
            select(DocumentRecord)
            .order_by(DocumentRecord.created_at.desc())
            .offset(page * page_size)
            .limit(page_size)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
