"""Classification modality."""
from ..models import IntentLabel, ModalityRequest, ModalityResponse
from .base import BaseModality, ICoreAI


class ClassificationModality(BaseModality):
    intent = IntentLabel.CLASSIFICATION

    async def execute(self, request: ModalityRequest, core_ai: ICoreAI) -> ModalityResponse:
        prompt = (
            f"Classify the following text into the most appropriate category.\n"
            f"Return ONLY the category label.\n\nText:\n{request.text}"
        )
        try:
            result = await core_ai.generate(prompt)
        except Exception as exc:
            return self.fallback_response(request, str(exc))
        return ModalityResponse(
            session_id=request.session_id,
            intent=self.intent,
            result={"label": result.strip()},
        )
