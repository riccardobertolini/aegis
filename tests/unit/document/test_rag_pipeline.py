"""Unit tests — RAGPipeline with mocked knowledge + inference."""
import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.domain.ports.knowledge import Document, SearchResult
from backend.infrastructure.document.rag_pipeline import RAGPipeline, RAGRequest


@pytest.fixture
def mock_knowledge():
    svc = AsyncMock()
    svc.search.return_value = [
        SearchResult(
            document=Document(id="doc1", content="The capital of France is Paris."),
            score=0.95,
        )
    ]
    return svc


@pytest.fixture
def mock_inference():
    svc = AsyncMock()
    svc.generate.return_value = MagicMock(text="Paris is the capital of France.")
    return svc


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def test_rag_run_returns_answer(mock_knowledge, mock_inference):
    pipeline = RAGPipeline(mock_knowledge, mock_inference, default_model_id="test-model")
    req = RAGRequest(question="What is the capital of France?")
    result = run(pipeline.run(req))
    assert "Paris" in result.answer
    assert result.retrieved_chunks == 1


def test_rag_run_includes_sources(mock_knowledge, mock_inference):
    pipeline = RAGPipeline(mock_knowledge, mock_inference)
    req = RAGRequest(question="Capital?", include_sources=True)
    result = run(pipeline.run(req))
    assert len(result.sources) == 1
    assert result.sources[0]["doc_id"] == "doc1"


def test_rag_run_no_sources_when_disabled(mock_knowledge, mock_inference):
    pipeline = RAGPipeline(mock_knowledge, mock_inference)
    req = RAGRequest(question="Capital?", include_sources=False)
    result = run(pipeline.run(req))
    assert result.sources == []


def test_rag_prompt_contains_context(mock_knowledge, mock_inference):
    pipeline = RAGPipeline(mock_knowledge, mock_inference)
    req = RAGRequest(question="Capital?")
    run(pipeline.run(req))
    call_args = mock_inference.generate.call_args
    prompt = call_args.kwargs.get("prompt") or call_args.args[0]
    assert "Paris" in prompt
    assert "Capital?" in prompt


def test_rag_empty_retrieval_handles_gracefully(mock_inference):
    knowledge = AsyncMock()
    knowledge.search.return_value = []
    pipeline = RAGPipeline(knowledge, mock_inference)
    req = RAGRequest(question="Unanswerable?")
    run(pipeline.run(req))
    # Should still call generate with "No relevant context found"
    call_args = mock_inference.generate.call_args
    prompt = call_args.kwargs.get("prompt") or call_args.args[0]
    assert "No relevant context" in prompt
