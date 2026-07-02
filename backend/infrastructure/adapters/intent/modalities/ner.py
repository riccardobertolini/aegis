"""Named Entity Recognition modality."""
from ..models import IntentLabel, ModalityRequest, ModalityResponse
from .base import BaseModality, ICoreAI


class NerModality(BaseModality):
    intent = IntentLabel.NER

    async def execute(self, request: ModalityRequest, core_ai: ICoreAI) -> ModalityResponse:
        prompt = (
            "Identify and list all named entities in the text below.\n"
            "Group them by type: PERSON, ORGANISATION, LOCATION, DATE, OTHER.\n"
            "Return JSON.\n\n"
            f"{request.text}"
        )
        try:
            result = await core_ai.generate(prompt)
        except Exception as exc:
            return self.fallback_response(request, str(exc))
        return ModalityResponse(
            session_id=request.session_id,
            intent=self.intent,
            result={"entities": result},
        )
