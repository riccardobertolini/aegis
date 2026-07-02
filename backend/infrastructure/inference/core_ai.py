"""CoreAIService — implements ICoreAIPort.

Orchestrates: Intent → Memory recall → Inference → Memory store.
All engines are injected via constructor (Dependency Injection).
"""
from __future__ import annotations

import logging
from typing import Optional

from backend.domain.ports.core_ai import AIRequest, AIResponse, ICoreAIPort
from backend.domain.ports.inference import IInferencePort, InferenceRequest
from backend.domain.ports.memory import IMemoryPort
from backend.domain.ports.intent import IIntentPort

logger = logging.getLogger(__name__)


class CoreAIService(ICoreAIPort):
    """Top-level AI pipeline:

        user_input
            └─ [IntentEngine]      detect intent + extract entities
            └─ [MemoryEngine]      recall relevant past turns
            └─ [InferenceEngine]   run SSM model
            └─ [MemoryEngine]      store new turn
            └─ AIResponse
    """

    def __init__(
        self,
        inference: IInferencePort,
        memory: Optional[IMemoryPort] = None,
        intent: Optional[IIntentPort] = None,
        default_model_id: str = "",
        system_prompt: str = "",
        max_context_turns: int = 10,
    ) -> None:
        self._inference = inference
        self._memory = memory
        self._intent = intent
        self._default_model_id = default_model_id
        self._system_prompt = system_prompt
        self._max_context_turns = max_context_turns

    async def process(self, request: AIRequest) -> AIResponse:
        trace: list[str] = []

        # 1. Intent detection (optional)
        intent_label = "chat"
        entities: dict = {}
        if self._intent is not None:
            try:
                intent_result = await self._intent.detect(request.user_input)
                intent_label = getattr(intent_result, "intent", "chat")
                entities = getattr(intent_result, "entities", {})
                trace.append(f"intent:{intent_label}")
            except Exception as exc:
                logger.warning("Intent detection failed: %s", exc)

        # 2. Memory recall (optional)
        history_turns: list[dict] = []
        if self._memory is not None:
            try:
                history_turns = await self._recall_memory(
                    request.session_id, request.user_input
                )
                trace.append(f"memory_recalled:{len(history_turns)}")
            except Exception as exc:
                logger.warning("Memory recall failed: %s", exc)

        # 3. Build prompt
        prompt = self._build_prompt(
            system=self._system_prompt,
            history=history_turns,
            user_input=request.user_input,
            context=request.context,
        )

        # 4. Run inference
        model_id = request.context.get("model_id", self._default_model_id)
        inf_request = InferenceRequest(
            prompt=prompt,
            model_id=model_id,
            max_tokens=request.context.get("max_tokens", 512),
            temperature=request.context.get("temperature", 0.7),
            stream=False,
            extra={
                "top_p": request.context.get("top_p", 1.0),
                "repetition_penalty": request.context.get("repetition_penalty", 1.0),
            },
        )
        inf_response = await self._inference.run(inf_request)
        trace.append(f"inference:{inf_response.model_id}")

        # 5. Store new turn in memory (optional)
        if self._memory is not None:
            try:
                await self._store_memory(
                    session_id=request.session_id,
                    user_input=request.user_input,
                    assistant_reply=inf_response.text,
                    context=request.context,
                )
                trace.append("memory_stored")
            except Exception as exc:
                logger.warning("Memory store failed: %s", exc)

        return AIResponse(
            session_id=request.session_id,
            text=inf_response.text,
            engine_trace=trace,
            metadata={
                "intent": intent_label,
                "entities": entities,
                "model_id": inf_response.model_id,
                "prompt_tokens": inf_response.prompt_tokens,
                "completion_tokens": inf_response.completion_tokens,
                "finish_reason": inf_response.finish_reason,
            },
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _recall_memory(
        self, session_id: str, user_input: str
    ) -> list[dict]:
        """Pull recent turns from memory. Returns list of {role, content}."""
        if self._memory is None:
            return []
        try:
            # IMemoryPort.search returns a list; fall back to get_history if absent
            if hasattr(self._memory, "get_history"):
                raw = await self._memory.get_history(  # type: ignore[attr-defined]
                    session_id=session_id,
                    limit=self._max_context_turns,
                )
            else:
                raw = await self._memory.search(  # type: ignore[attr-defined]
                    query=user_input,
                    session_id=session_id,
                    top_k=self._max_context_turns,
                )
            return [
                {"role": getattr(e, "role", "user"), "content": getattr(e, "content", str(e))}
                for e in (raw or [])
            ]
        except Exception:
            return []

    async def _store_memory(
        self,
        session_id: str,
        user_input: str,
        assistant_reply: str,
        context: dict,
    ) -> None:
        if self._memory is None:
            return
        assistant_id = context.get("assistant_id", "default")
        user_id = context.get("user_id", "anonymous")
        if hasattr(self._memory, "add_entry"):
            await self._memory.add_entry(  # type: ignore[attr-defined]
                session_id=session_id,
                assistant_id=assistant_id,
                user_id=user_id,
                role="user",
                content=user_input,
            )
            await self._memory.add_entry(
                session_id=session_id,
                assistant_id=assistant_id,
                user_id=user_id,
                role="assistant",
                content=assistant_reply,
            )
        elif hasattr(self._memory, "store"):
            await self._memory.store(  # type: ignore[attr-defined]
                session_id=session_id,
                user_message=user_input,
                assistant_message=assistant_reply,
            )

    @staticmethod
    def _build_prompt(
        system: str,
        history: list[dict],
        user_input: str,
        context: dict,
    ) -> str:
        """Assemble the full prompt string.

        Format (simple ChatML-style, compatible with Mamba defaults)::

            <|system|>\n{system}\n
            <|user|>\n{turn1_user}\n
            <|assistant|>\n{turn1_assistant}\n
            ...
            <|user|>\n{user_input}\n
            <|assistant|>\n
        """
        parts: list[str] = []

        if system:
            parts.append(f"<|system|>\n{system}\n")

        for turn in history:
            role = turn.get("role", "user")
            content = turn.get("content", "")
            parts.append(f"<|{role}|>\n{content}\n")

        parts.append(f"<|user|>\n{user_input}\n<|assistant|>\n")
        return "".join(parts)
