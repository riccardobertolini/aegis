"""RAG modality: retrieves context from KBs then answers via CoreAI."""
from __future__ import annotations

from ..models import IntentLabel, ModalityRequest, ModalityResponse
from .base import BaseModality, ICoreAI


class RagModality(BaseModality):
    intent = IntentLabel.RAG

    def __init__(self, knowledge_engine=None) -> None:
        # knowledge_engine injected at runtime; if None, falls back to plain QA
        self._ke = knowledge_engine

    async def execute(self, request: ModalityRequest, core_ai: ICoreAI) -> ModalityResponse:
        citations: list[dict] = []
        context_text = ""

        if self._ke and request.kb_ids:
            try:
                rag_ctx = self._ke.build_rag_context(
                    query=request.text,
                    kb_ids=request.kb_ids,
                    top_k=request.parameters.get("top_k", 5),
                )
                context_text = rag_ctx.context_text
                citations     = rag_ctx.citations
            except Exception:  # noqa: BLE001
                pass  # degrade gracefully to plain QA

        prompt = (
            f"Answer the following question using the provided context if available.\n\n"
            f"Context:\n{context_text or '(none)'}\n\n"
            f"Question: {request.text}"
        )
        try:
            result = await core_ai.generate(prompt)
        except Exception as exc:
            return self.fallback_response(request, str(exc))
        return ModalityResponse(
            session_id=request.session_id,
            intent=self.intent,
            result={"answer": result},
            citations=citations,
            fallback_used=(context_text == ""),
        )
