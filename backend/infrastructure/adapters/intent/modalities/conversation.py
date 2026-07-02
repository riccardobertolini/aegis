"""Conversational assistant modality."""
from ..models import IntentLabel, ModalityRequest, ModalityResponse
from .base import BaseModality, ICoreAI


class ConversationModality(BaseModality):
    intent = IntentLabel.CONVERSATION

    async def execute(self, request: ModalityRequest, core_ai: ICoreAI) -> ModalityResponse:
        history = request.context.get("history", [])
        history_block = ""
        if history:
            turns = [f"{t['role'].capitalize()}: {t['content']}" for t in history[-6:]]
            history_block = "\n".join(turns) + "\n"
        prompt = (
            f"{history_block}"
            f"User: {request.text}\n"
            f"Assistant:"
        )
        try:
            result = await core_ai.generate(prompt)
        except Exception as exc:
            return self.fallback_response(request, str(exc))
        return ModalityResponse(
            session_id=request.session_id,
            intent=self.intent,
            result={"reply": result},
        )
