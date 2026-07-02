"""Log analysis modality."""
from ..models import IntentLabel, ModalityRequest, ModalityResponse
from .base import BaseModality, ICoreAI


class LogAnalysisModality(BaseModality):
    intent = IntentLabel.LOG_ANALYSIS

    async def execute(self, request: ModalityRequest, core_ai: ICoreAI) -> ModalityResponse:
        prompt = (
            "Analyse the following log entries.\n"
            "Identify errors, warnings, patterns and provide a structured summary.\n\n"
            f"{request.text}"
        )
        try:
            result = await core_ai.generate(prompt)
        except Exception as exc:
            return self.fallback_response(request, str(exc))
        return ModalityResponse(
            session_id=request.session_id,
            intent=self.intent,
            result={"log_summary": result},
        )
