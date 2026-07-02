"""Unit tests for DocumentContainer wiring."""
from __future__ import annotations

import pytest
from pathlib import Path
from unittest.mock import MagicMock

from backend.infrastructure.rag.container import DocumentContainer
from backend.domain.ports.document import IDocumentPort
from backend.domain.ports.knowledge import IKnowledgePort
from backend.infrastructure.rag.rag_service import RAGService


def _null_inference():
    m = MagicMock()
    return m


@pytest.fixture()
def container(tmp_path: Path):
    try:
        import chromadb  # noqa
    except ImportError:
        pytest.skip("chromadb not installed")
    return DocumentContainer.build(
        data_dir=tmp_path / "data",
        inference=_null_inference(),
        models_root=tmp_path / "models",
        embed_model="all-MiniLM-L6-v2",
    )


def test_document_service_is_idocument_port(container):
    assert isinstance(container.document_service, IDocumentPort)


def test_knowledge_is_iknowledge_port(container):
    assert isinstance(container.knowledge, IKnowledgePort)


def test_rag_service_type(container):
    assert isinstance(container.rag_service, RAGService)
