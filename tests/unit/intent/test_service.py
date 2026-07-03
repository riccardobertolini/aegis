"""Unit tests for IntentService hybrid flow."""
from unittest.mock import AsyncMock

import pytest

from backend.domain.ports.intent import IntentMode, IntentRequest
from backend.domain.ports.knowledge import Document, SearchResult
from backend.infrastructure.intent.rules import HeuristicIntentClassifier
from backend.infrastructure.intent.service import IntentService


@pytest.mark.asyncio
async def test_intent_service_heuristic_only():
    svc = IntentService(heuristic=HeuristicIntentClassifier(), ssm=None, knowledge=None)
    result = await svc.classify(IntentRequest(text="list models", session_id="s1"))
    assert result.intent == "list_models"
    assert result.mode == IntentMode.HEURISTIC
    assert result.suggested_engine == "inference"


@pytest.mark.asyncio
async def test_intent_service_hybrid_uses_ssm_override():
    heuristic = HeuristicIntentClassifier()
    ssm = AsyncMock()
    ssm.classify.return_value = {
        "intent": "question_answering",
        "confidence": 0.88,
        "entities": {"domain": "docs"},
        "suggested_engine": "knowledge+inference",
    }
    svc = IntentService(heuristic=heuristic, ssm=ssm, knowledge=None)
    result = await svc.classify(IntentRequest(text="spiegami questo", session_id="s1"))
    assert result.intent == "question_answering"
    assert result.mode == IntentMode.HYBRID
    assert result.entities["domain"] == "docs"
    assert result.suggested_engine == "knowledge+inference"


@pytest.mark.asyncio
async def test_intent_service_knowledge_peek_enriches_entities():
    heuristic = HeuristicIntentClassifier()
    knowledge = AsyncMock()
    knowledge.search.return_value = [
        SearchResult(document=Document(id="doc-1", content="manuale"), score=0.91)
    ]
    svc = IntentService(heuristic=heuristic, ssm=None, knowledge=knowledge)
    result = await svc.classify(IntentRequest(text="cerca nel manuale", session_id="s1"))
    assert result.entities["knowledge_hit"] is True
    assert result.entities["top_document_id"] == "doc-1"


@pytest.mark.asyncio
async def test_intent_service_needs_clarification_below_threshold():
    heuristic = HeuristicIntentClassifier()
    svc = IntentService(heuristic=heuristic, ssm=None, knowledge=None, clarification_threshold=0.8)
    result = await svc.classify(IntentRequest(text="ciao", session_id="s1"))
    assert result.needs_clarification is True
    assert result.clarification_question is not None
