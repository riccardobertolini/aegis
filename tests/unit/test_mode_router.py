"""Unit tests for ModeRouter and all modalities (mock CoreAI)."""
import asyncio

import pytest

from backend.infrastructure.adapters.intent.models import IntentLabel, ModalityRequest
from backend.infrastructure.adapters.intent.mode_router import ModeRouter


class MockCoreAI:
    """Deterministic fake that echoes the prompt."""
    async def generate(self, prompt: str, **kwargs) -> str:
        return f"[mock_result] {prompt[:60]}"


@pytest.fixture
def router():
    return ModeRouter()


@pytest.fixture
def core_ai():
    return MockCoreAI()


def _req(intent: IntentLabel, text: str = "test input", **kwargs) -> ModalityRequest:
    return ModalityRequest(
        session_id="sess-test",
        intent=intent,
        text=text,
        **kwargs,
    )


# ------------------------------------------------------------------ #
# Each modality executes without error                                 #
# ------------------------------------------------------------------ #

@pytest.mark.parametrize("intent", [
    IntentLabel.CLASSIFICATION,
    IntentLabel.DOCUMENT_ANALYSIS,
    IntentLabel.EXTRACTION,
    IntentLabel.NER,
    IntentLabel.SUMMARY,
    IntentLabel.TRANSLATION,
    IntentLabel.REWRITE,
    IntentLabel.QA,
    IntentLabel.CONVERSATION,
    IntentLabel.TIMESERIES,
    IntentLabel.LOG_ANALYSIS,
])
def test_modality_executes(router, core_ai, intent):
    req = _req(intent)
    resp = asyncio.get_event_loop().run_until_complete(router.route(req, core_ai))
    assert resp.session_id == "sess-test"
    assert resp.error is None
    assert resp.result is not None


def test_rag_modality_no_ke(router, core_ai):
    """RAG without KE degrades gracefully (plain QA)."""
    req = _req(IntentLabel.RAG, kb_ids=[])
    resp = asyncio.get_event_loop().run_until_complete(router.route(req, core_ai))
    assert resp.result is not None
    assert resp.fallback_used is True  # no KB provided → no context


def test_speech_modality_without_adapter(router, core_ai):
    req = _req(IntentLabel.SPEECH)
    resp = asyncio.get_event_loop().run_until_complete(router.route(req, core_ai))
    assert resp.fallback_used is True
    assert "SpeechAdapter" in (resp.error or "")


# ------------------------------------------------------------------ #
# Feature flags                                                        #
# ------------------------------------------------------------------ #

def test_disabled_intent_falls_back_to_conversation(router, core_ai):
    router.disable(IntentLabel.SUMMARY)
    req = _req(IntentLabel.SUMMARY, text="hello from disabled modality")
    resp = asyncio.get_event_loop().run_until_complete(router.route(req, core_ai))
    assert resp.fallback_used is True
    assert resp.metadata.get("original_intent") == IntentLabel.SUMMARY


def test_enable_disable_roundtrip(router):
    router.disable(IntentLabel.NER)
    assert not router.is_enabled(IntentLabel.NER)
    router.enable(IntentLabel.NER)
    assert router.is_enabled(IntentLabel.NER)


def test_enabled_intents_list(router):
    intents = router.enabled_intents()
    assert IntentLabel.UNKNOWN not in intents
    assert IntentLabel.CONVERSATION in intents


# ------------------------------------------------------------------ #
# UNKNOWN intent                                                       #
# ------------------------------------------------------------------ #

def test_unknown_intent_is_disabled_by_default(router, core_ai):
    req = _req(IntentLabel.UNKNOWN, text="???")
    resp = asyncio.get_event_loop().run_until_complete(router.route(req, core_ai))
    assert resp.fallback_used is True
