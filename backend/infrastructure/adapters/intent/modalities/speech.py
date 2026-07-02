"""Speech modality stub — delegates to ISpeechPort adapter."""
from ..models import IntentLabel, ModalityRequest, ModalityResponse
from .base import BaseModality, ICoreAI


class SpeechModality(BaseModality):
    intent = IntentLabel.SPEECH

    def __init__(self, speech_adapter=None) -> None:
        self._speech = speech_adapter

    async def execute(self, request: ModalityRequest, core_ai: ICoreAI) -> ModalityResponse:
        if self._speech is None:
            return self.fallback_response(
                request,
                "SpeechAdapter not configured. "
                "Attach a concrete ISpeechPort implementation.",
            )
        try:
            # speech_adapter.transcribe(path) returns plain text
            path = request.parameters.get("audio_path", "")
            transcript = await self._speech.transcribe(path)
        except Exception as exc:
            return self.fallback_response(request, str(exc))
        return ModalityResponse(
            session_id=request.session_id,
            intent=self.intent,
            result={"transcript": transcript},
        )
