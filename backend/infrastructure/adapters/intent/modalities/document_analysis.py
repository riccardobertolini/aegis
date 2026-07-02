"""Document analysis modality."""
from ..models import IntentLabel, ModalityRequest, ModalityResponse
from .base import BaseModality, ICoreAI


class DocumentAnalysisModality(BaseModality):
    intent = IntentLabel.DOCUMENT_ANALYSIS

    async def execute(self, request: ModalityRequest, core_ai: ICoreAI) -> ModalityResponse:
        docs_note = ""
        if request.documents:
            docs_note = f"\nDocuments: {', '.join(request.documents)}"
        prompt = (
            f"Analyse the following document and provide key insights, "
            f"main topics and a brief summary.{docs_note}\n\n{request.text}"
        )
        try:
            result = await core_ai.generate(prompt)
        except Exception as exc:
            return self.fallback_response(request, str(exc))
        return ModalityResponse(
            session_id=request.session_id,
            intent=self.intent,
            result={"analysis": result},
        )
