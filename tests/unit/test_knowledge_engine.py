"""Unit tests for KnowledgeEngine (with mocked dependencies)."""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

FIXTURES = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def mock_embedding():
    """Return a deterministic fake embedding engine."""
    emb = MagicMock()
    emb.embed.side_effect = lambda texts: [[0.1] * 384 for _ in texts]
    emb.embed_one.return_value = [0.1] * 384
    return emb


@pytest.fixture
def mock_store():
    store = MagicMock()
    store.count.return_value = 0
    store.query.return_value = []
    return store


@pytest.fixture
def engine(mock_embedding, mock_store):
    from backend.infrastructure.adapters.knowledge.knowledge_engine import KnowledgeEngine
    from backend.infrastructure.adapters.document.document_engine import DocumentEngine

    return KnowledgeEngine(
        document_engine=DocumentEngine(chunk_size=200, overlap=20),
        embedding_engine=mock_embedding,
        vector_store=mock_store,
    )


def test_create_and_list_kb(engine):
    kb = engine.create_kb("test-kb", description="Test", category="unit")
    assert kb.kb_id
    kbs = engine.list_kbs()
    assert any(k.kb_id == kb.kb_id for k in kbs)


def test_list_kbs_filter_category(engine):
    engine.create_kb("kb-a", category="cat-a")
    engine.create_kb("kb-b", category="cat-b")
    result = engine.list_kbs(category="cat-a")
    assert all(k.category == "cat-a" for k in result)


def test_add_document_indexes_chunks(engine, mock_store):
    kb = engine.create_kb("ingest-kb")
    count = engine.add_document(kb.kb_id, FIXTURES / "sample.txt")
    assert count > 0
    mock_store.upsert.assert_called_once()


def test_retrieve_calls_store(engine, mock_store):
    kb = engine.create_kb("retrieve-kb")
    engine.retrieve(kb.kb_id, "hello world")
    mock_store.query.assert_called_once()


def test_build_rag_context(engine):
    from backend.infrastructure.adapters.knowledge.models import RetrievedChunk

    kb = engine.create_kb("rag-kb")
    fake_chunk = RetrievedChunk(
        chunk_id="c1",
        document_id="d1",
        source_path="/fake/doc.txt",
        text="Relevant content about Aegis.",
        score=0.92,
        kb_id=kb.kb_id,
    )
    engine._store.query.return_value = [fake_chunk]
    ctx = engine.build_rag_context("What is Aegis?", [kb.kb_id])
    assert "Relevant content" in ctx.context_text
    assert len(ctx.citations) == 1


def test_delete_kb(engine, mock_store):
    kb = engine.create_kb("del-kb")
    engine.delete_kb(kb.kb_id)
    with pytest.raises(KeyError):
        engine.get_kb(kb.kb_id)
    mock_store.delete_collection.assert_called_with(kb.kb_id)


def test_integrity_check(engine, mock_store):
    kb = engine.create_kb("integrity-kb")
    mock_store.count.return_value = 0
    result = engine.integrity_check(kb.kb_id)
    assert result["kb_id"] == kb.kb_id
    assert "consistent" in result
