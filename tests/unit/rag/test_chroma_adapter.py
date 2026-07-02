"""Unit tests for ChromaKnowledgeAdapter (mock embedder + in-memory Chroma)."""
from __future__ import annotations

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock
from pathlib import Path

from backend.domain.ports.knowledge import Document, SearchQuery
from backend.infrastructure.rag.chunker import TextChunker


def _make_embedder(dim: int = 8) -> MagicMock:
    emb = MagicMock()
    emb.embed_texts = AsyncMock(
        side_effect=lambda texts: [[0.1 * (i % 10)] * dim for i in range(len(texts))]
    )
    emb.embed_query = AsyncMock(return_value=[0.1] * dim)
    return emb


@pytest.fixture()
def chroma_adapter(tmp_path: Path):
    try:
        import chromadb  # noqa: F401
    except ImportError:
        pytest.skip("chromadb not installed")

    from backend.infrastructure.rag.chroma_adapter import ChromaKnowledgeAdapter
    return ChromaKnowledgeAdapter(
        persist_dir=str(tmp_path / "chroma"),
        embedder=_make_embedder(),
        chunker=TextChunker(chunk_size=64, chunk_overlap=8),
        collection_name="test_col",
    )


@pytest.mark.asyncio
async def test_ingest_and_list(chroma_adapter):
    docs = [
        Document(id="d1", content="The quick brown fox jumps.", metadata={"source": "test"}),
        Document(id="d2", content="Hello Aegis AI platform.", metadata={"source": "test"}),
    ]
    await chroma_adapter.ingest(docs)
    listed = await chroma_adapter.list_documents(page=0, page_size=10)
    ids = [d.id for d in listed]
    assert "d1" in ids or "d2" in ids  # at least one persisted


@pytest.mark.asyncio
async def test_search_returns_results(chroma_adapter):
    docs = [Document(id="d3", content="Python is great for AI.", metadata={})]
    await chroma_adapter.ingest(docs)
    results = await chroma_adapter.search(SearchQuery(text="Python AI", top_k=3))
    assert isinstance(results, list)


@pytest.mark.asyncio
async def test_delete_removes_document(chroma_adapter):
    docs = [Document(id="del1", content="Delete me please.", metadata={})]
    await chroma_adapter.ingest(docs)
    await chroma_adapter.delete("del1")
    listed = await chroma_adapter.list_documents()
    assert all(d.id != "del1" for d in listed)


@pytest.mark.asyncio
async def test_ingest_empty_noop(chroma_adapter):
    # Should not raise
    await chroma_adapter.ingest([])
