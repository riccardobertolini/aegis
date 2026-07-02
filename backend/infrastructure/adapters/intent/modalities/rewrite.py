"""Text rewriting / paraphrasing modality."""
from ..models import IntentLabel, ModalityRequest, ModalityResponse
from .base import BaseModality, ICoreAI


class RewriteModality(BaseModality):
    intent = IntentLabel.REWRITE

    async def execute(self, request: ModalityRequest, core_ai: ICoreAI) -> ModalityResponse:
        style = request.parameters.get("style", "clear and professional")
        prompt = (
            f"Rewrite the following text in a {style} style.\n"
            f"Preserve the original meaning.\n\n"
            f"{request.text}"
        )
        try:
            result = await core_ai.generate(prompt)
        except Exception as exc:
            return self.fallback_response(request, str(exc))
        return ModalityResponse(
            session_id=request.session_id,
            intent=self.intent,
            result={"rewritten": result, "style": style},
        )
