"""Translation modality."""
from ..models import IntentLabel, ModalityRequest, ModalityResponse
from .base import BaseModality, ICoreAI


class TranslationModality(BaseModality):
    intent = IntentLabel.TRANSLATION

    async def execute(self, request: ModalityRequest, core_ai: ICoreAI) -> ModalityResponse:
        target_lang = request.parameters.get("target_language", "English")
        prompt = (
            f"Translate the following text to {target_lang}.\n"
            f"Return ONLY the translation, no explanations.\n\n"
            f"{request.text}"
        )
        try:
            result = await core_ai.generate(prompt)
        except Exception as exc:
            return self.fallback_response(request, str(exc))
        return ModalityResponse(
            session_id=request.session_id,
            intent=self.intent,
            result={"translation": result, "target_language": target_lang},
        )
