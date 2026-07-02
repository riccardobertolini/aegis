"""Time-series analysis modality."""
from ..models import IntentLabel, ModalityRequest, ModalityResponse
from .base import BaseModality, ICoreAI


class TimeseriesModality(BaseModality):
    intent = IntentLabel.TIMESERIES

    async def execute(self, request: ModalityRequest, core_ai: ICoreAI) -> ModalityResponse:
        analysis_type = request.parameters.get("analysis_type", "trend and anomaly detection")
        prompt = (
            f"Perform {analysis_type} on the following time-series data.\n"
            f"Identify trends, seasonality, anomalies and provide insights.\n\n"
            f"{request.text}"
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
