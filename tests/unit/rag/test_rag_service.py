"""Unit tests for RAGService."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock

from backend.domain.ports.knowledge import SearchResult, Document
from backend.domain.ports.inference import InferenceResponse
from backend.infrastructure.rag.rag_service import RAGService, RAGRequest


def _make_knowledge_mock(results=None) -> MagicMock:
    m = MagicMock()
    m.search = AsyncMock(return_value=results or [])
    m.ingest = AsyncMock()
    return m


def _make_inference_mock(text="RAG answer") -> MagicMock:
    m = MagicMock()
    m.run = AsyncMock(return_value=InferenceResponse(
        text=text, model_id="test", prompt_tokens=10, completion_tokens=5, finish_reason="stop"
    ))
    return m


@pytest.mark.asyncio
async def test_rag_query_no_context():
    svc = RAGService(
        knowledge=_make_knowledge_mock([]),
        inference=_make_inference_mock("No context answer"),
        default_model_id="m",
    )
    resp = await svc.query(RAGRequest(query="What is Aegis?"))
    assert resp.answer == "No context answer"
    assert resp.sources == []


@pytest.mark.asyncio
async def test_rag_query_with_results():
    results = [
        SearchResult(
            document=Document(id="d1", content="Aegis is an offline AI platform.", metadata={}),
            score=0.9,
        )
    ]
    svc = RAGService(
        knowledge=_make_knowledge_mock(results),
        inference=_make_inference_mock("Aegis is offline."),
        default_model_id="m",
    )
    resp = await svc.query(RAGRequest(query="What is Aegis?", include_sources=True))
    assert resp.answer == "Aegis is offline."
    assert len(resp.sources) == 1
    assert resp.sources[0].document_id == "d1"
    assert resp.sources[0].score == 0.9


@pytest.mark.asyncio
async def test_rag_excludes_sources_when_disabled():
    results = [
        SearchResult(
            document=Document(id="d2", content="Some content", metadata={}),
            score=0.8,
        )
    ]
    svc = RAGService(
        knowledge=_make_knowledge_mock(results),
        inference=_make_inference_mock("answer"),
        default_model_id="m",
    )
    resp = await svc.query(RAGRequest(query="q", include_sources=False))
    assert resp.sources == []


@pytest.mark.asyncio
async def test_rag_inference_failure_returns_error_message():
    knowledge = _make_knowledge_mock([])
    inf = MagicMock()
    inf.run = AsyncMock(side_effect=RuntimeError("GPU OOM"))
    svc = RAGService(knowledge=knowledge, inference=inf, default_model_id="m")
    resp = await svc.query(RAGRequest(query="crash"))
    assert "Inference error" in resp.answer


@pytest.mark.asyncio
async def test_rag_prompt_contains_context():
    """Verify the context is actually injected into the prompt."""
    captured = []

    async def _capture(req):
        captured.append(req.prompt)
        return InferenceResponse(text="ok", model_id="m", prompt_tokens=1, completion_tokens=1, finish_reason="stop")

    inf = MagicMock()
    inf.run = _capture

    results = [
        SearchResult(
            document=Document(id="d3", content="UNIQUE_CONTEXT_TOKEN", metadata={}),
            score=0.95,
        )
    ]
    svc = RAGService(knowledge=_make_knowledge_mock(results), inference=inf, default_model_id="m")
    await svc.query(RAGRequest(query="test"))
    assert len(captured) == 1
    assert "UNIQUE_CONTEXT_TOKEN" in captured[0]
