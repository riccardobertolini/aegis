"""Unit tests for CoreAIService."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.domain.ports.core_ai import AIRequest
from backend.domain.ports.inference import InferenceRequest, InferenceResponse
from backend.infrastructure.inference.core_ai import CoreAIService

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_inference_mock(text: str = "Hello from Mamba") -> MagicMock:
    mock = MagicMock()
    mock.run = AsyncMock(return_value=InferenceResponse(
        text=text,
        model_id="test-model",
        prompt_tokens=10,
        completion_tokens=8,
        finish_reason="stop",
    ))
    return mock


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_process_returns_ai_response():
    service = CoreAIService(
        inference=_make_inference_mock(),
        default_model_id="test-model",
    )
    req = AIRequest(session_id="s1", user_input="What is Mamba?")
    resp = await service.process(req)
    assert resp.session_id == "s1"
    assert resp.text == "Hello from Mamba"
    assert "inference:test-model" in resp.engine_trace


@pytest.mark.asyncio
async def test_process_with_system_prompt_builds_correct_prompt():
    """Verify that the system prompt appears in the forwarded InferenceRequest."""
    captured: list[InferenceRequest] = []

    async def _capture_run(req: InferenceRequest) -> InferenceResponse:
        captured.append(req)
        return InferenceResponse(
            text="ok", model_id="m", prompt_tokens=5, completion_tokens=2, finish_reason="stop"
        )

    mock = MagicMock()
    mock.run = _capture_run

    service = CoreAIService(
        inference=mock,
        default_model_id="m",
        system_prompt="You are a pirate.",
    )
    await service.process(AIRequest(session_id="s", user_input="ahoy"))
    assert len(captured) == 1
    assert "<|system|>" in captured[0].prompt
    assert "You are a pirate." in captured[0].prompt
    assert "ahoy" in captured[0].prompt


@pytest.mark.asyncio
async def test_process_engine_trace_contains_intent_when_provided():
    from unittest.mock import AsyncMock as AM

    intent_mock = MagicMock()
    intent_result = MagicMock()
    intent_result.intent = "question"
    intent_result.entities = {}
    intent_mock.detect = AM(return_value=intent_result)

    service = CoreAIService(
        inference=_make_inference_mock(),
        intent=intent_mock,
        default_model_id="m",
    )
    resp = await service.process(AIRequest(session_id="s", user_input="test"))
    assert any("intent:" in t for t in resp.engine_trace)


@pytest.mark.asyncio
async def test_process_gracefully_handles_memory_failure():
    """Memory engine failure must not crash the pipeline."""
    from unittest.mock import AsyncMock as AM

    memory_mock = MagicMock()
    memory_mock.get_history = AM(side_effect=RuntimeError("DB down"))
    memory_mock.add_entry = AM(side_effect=RuntimeError("DB down"))

    service = CoreAIService(
        inference=_make_inference_mock(),
        memory=memory_mock,
        default_model_id="m",
    )
    resp = await service.process(AIRequest(session_id="s", user_input="test"))
    assert resp.text == "Hello from Mamba"  # pipeline completed despite memory errors


@pytest.mark.asyncio
async def test_build_prompt_no_system_no_history():
    prompt = CoreAIService._build_prompt(
        system="",
        history=[],
        user_input="hello",
        context={},
    )
    assert prompt == "<|user|>\nhello\n<|assistant|>\n"


@pytest.mark.asyncio
async def test_build_prompt_with_history():
    history = [
        {"role": "user", "content": "first turn"},
        {"role": "assistant", "content": "first reply"},
    ]
    prompt = CoreAIService._build_prompt(
        system="sys",
        history=history,
        user_input="second turn",
        context={},
    )
    assert "<|system|>" in prompt
    assert "first turn" in prompt
    assert "first reply" in prompt
    assert "second turn" in prompt
