"""Summarisation modality."""
from ..models import IntentLabel, ModalityRequest, ModalityResponse
from .base import BaseModality, ICoreAI


class SummaryModality(BaseModality):
    intent = IntentLabel.SUMMARY

    async def execute(self, request: ModalityRequest, core_ai: ICoreAI) -> ModalityResponse:
        max_sentences = request.parameters.get("max_sentences", 5)
        prompt = (
            f"Summarise the following text in at most {max_sentences} sentences.\n\n"
            f"{request.text}"
        )
        try:
            result = await core_ai.generate(prompt)
        except Exception as exc:
            return self.fallback_response(request, str(exc))
        return ModalityResponse(
            session_id=request.session_id,
            intent=self.intent,
            result={"summary": result},
        )
