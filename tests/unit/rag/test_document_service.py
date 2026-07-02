"""Unit tests for DocumentService."""
from __future__ import annotations

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock

from backend.infrastructure.rag.parser import DocumentParser
from backend.infrastructure.rag.document_service import DocumentService


def _make_knowledge_mock() -> MagicMock:
    m = MagicMock()
    m.ingest = AsyncMock()
    m.delete = AsyncMock()
    m.list_documents = AsyncMock(return_value=[])
    return m


@pytest.fixture()
def service() -> DocumentService:
    return DocumentService(
        parser=DocumentParser(),
        knowledge=_make_knowledge_mock(),
        document_repo=None,
    )


@pytest.mark.asyncio
async def test_ingest_bytes_returns_parsed_doc(service: DocumentService):
    data = b"Hello world. This is a test."
    doc = await service.ingest_bytes(data, "test.txt")
    assert doc.id.startswith("doc_")
    assert doc.filename == "test.txt"
    assert doc.mime_type == "text/plain"


@pytest.mark.asyncio
async def test_ingest_calls_knowledge_ingest(service: DocumentService):
    data = b"Some content to embed."
    await service.ingest_bytes(data, "embed.txt")
    service._knowledge.ingest.assert_called_once()


@pytest.mark.asyncio
async def test_delete_calls_knowledge_delete(service: DocumentService):
    await service.delete("doc_abc123")
    service._knowledge.delete.assert_called_once_with("doc_abc123")


@pytest.mark.asyncio
async def test_list_documents_empty_initially(service: DocumentService):
    docs = await service.list_documents()
    assert docs == []


@pytest.mark.asyncio
async def test_ingest_stores_in_mem_without_repo(service: DocumentService):
    data = b"In-memory doc."
    doc = await service.ingest_bytes(data, "mem.txt")
    docs = await service.list_documents()
    assert any(d.id == doc.id for d in docs)
