"""Structured data extraction modality."""
from ..models import IntentLabel, ModalityRequest, ModalityResponse
from .base import BaseModality, ICoreAI


class ExtractionModality(BaseModality):
    intent = IntentLabel.EXTRACTION

    async def execute(self, request: ModalityRequest, core_ai: ICoreAI) -> ModalityResponse:
        fields = request.parameters.get("fields", [])
        fields_note = f"Fields to extract: {fields}.\n" if fields else ""
        prompt = (
            f"Extract structured data from the following text.\n"
            f"{fields_note}"
            f"Return a JSON object with the extracted fields.\n\n{request.text}"
        )
        try:
            result = await core_ai.generate(prompt)
        except Exception as exc:
            return self.fallback_response(request, str(exc))
        return ModalityResponse(
            session_id=request.session_id,
            intent=self.intent,
            result={"extracted": result},
        )
