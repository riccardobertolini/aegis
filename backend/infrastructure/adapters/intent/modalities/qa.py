"""Question Answering modality."""
from ..models import IntentLabel, ModalityRequest, ModalityResponse
from .base import BaseModality, ICoreAI


class QaModality(BaseModality):
    intent = IntentLabel.QA

    async def execute(self, request: ModalityRequest, core_ai: ICoreAI) -> ModalityResponse:
        context = request.parameters.get("context", "")
        context_block = f"\nContext:\n{context}\n" if context else ""
        prompt = (
            f"Answer the following question accurately and concisely."
            f"{context_block}\n"
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
        )
