"""CoreAIService — top-level AI pipeline orchestrator.

In FASE 1 this only wires:
  user_input → InferenceEngine → response

In later phases it will extend to:
  user_input → IntentEngine → route(Knowledge | Memory | Inference | Translation …)

This file is the single point of change when new engines are added.
"""
from __future__ import annotations

import structlog

from backend.application.inference.inference_engine import InferenceEngine
from backend.domain.ports.core_ai import AIRequest, AIResponse, ICoreAIPort
from backend.domain.ports.inference import InferenceRequest

log = structlog.get_logger(__name__)

_DEFAULT_MODEL = "default"  # overridden by config in later phases


class CoreAIService(ICoreAIPort):
    """
    Implements ICoreAIPort for FASE 1.

    Only inference is wired. Other engines are no-ops pending their phases.
    """

    def __init__(
        self,
        inference_engine: InferenceEngine,
        default_model_id: str = _DEFAULT_MODEL,
    ) -> None:
        self._inference = inference_engine
        self._default_model_id = default_model_id

    async def process(self, request: AIRequest) -> AIResponse:
        log.info(
            "core_ai.process",
            session_id=request.session_id,
            input_len=len(request.user_input),
        )
        model_id = request.context.get("model_id", self._default_model_id)

        inf_req = InferenceRequest(
            prompt=request.user_input,
            model_id=model_id,
            max_tokens=request.context.get("max_tokens", 512),
            temperature=request.context.get("temperature", 0.7),
            extra={"session_id": request.session_id},
        )
        response = await self._inference.run(inf_req)

        return AIResponse(
            session_id=request.session_id,
            text=response.text,
            engine_trace=["inference"],
            metadata={
                "model_id": response.model_id,
                "prompt_tokens": response.prompt_tokens,
                "completion_tokens": response.completion_tokens,
            },
        )
