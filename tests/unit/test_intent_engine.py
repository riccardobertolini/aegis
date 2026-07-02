"""Integration-style test for IntentEngine (classify + route)."""
import asyncio

import pytest

from backend.infrastructure.adapters.intent.intent_engine import IntentEngine
from backend.infrastructure.adapters.intent.models import IntentLabel


class MockCoreAI:
    async def generate(self, prompt: str, **kwargs) -> str:
        return "[ok]"


@pytest.fixture
def engine():
    return IntentEngine(core_ai=MockCoreAI())


def test_run_returns_response(engine):
    resp = asyncio.get_event_loop().run_until_complete(
        engine.run("sess-1", "summarize this document")
    )
    assert resp.session_id == "sess-1"
    assert resp.error is None


def test_force_intent_bypasses_classifier(engine):
    resp = asyncio.get_event_loop().run_until_complete(
        engine.run("sess-2", "random text", force_intent=IntentLabel.SUMMARY)
    )
    assert resp.intent == IntentLabel.SUMMARY


def test_disable_then_enable_modality(engine):
    engine.disable_modality(IntentLabel.TRANSLATION)
    assert IntentLabel.TRANSLATION not in engine.enabled_modalities()
    engine.enable_modality(IntentLabel.TRANSLATION)
    assert IntentLabel.TRANSLATION in engine.enabled_modalities()


def test_classify_only(engine):
    from backend.domain.ports.intent import IntentRequest
    req = IntentRequest(text="translate to french", session_id="sess-3")
    result = asyncio.get_event_loop().run_until_complete(engine.classify(req))
    assert result.intent == IntentLabel.TRANSLATION.value
    assert result.confidence > 0
