"""SpeechService — composes STT + TTS, implements ISpeechPort."""
from __future__ import annotations

from pathlib import Path

from backend.domain.ports.speech import (
    ISpeechPort,
    SynthesisRequest,
    SynthesisResult,
    TranscriptionRequest,
    TranscriptionResult,
)
from backend.infrastructure.speech.stt import WhisperSTTService
from backend.infrastructure.speech.tts import CoquiTTSService


class SpeechService(ISpeechPort):
    def __init__(self, models_root: Path):
        stt_root = models_root / "whisper"
        tts_root = models_root / "tts"
        self._stt = WhisperSTTService(models_root=stt_root)
        self._tts = CoquiTTSService(models_root=tts_root)

    async def transcribe(self, request: TranscriptionRequest) -> TranscriptionResult:
        return await self._stt.transcribe(request)

    async def synthesize(self, request: SynthesisRequest) -> SynthesisResult:
        return await self._tts.synthesize(request)

    async def list_stt_models(self) -> list[str]:
        return self._stt.list_stt_models()

    async def list_tts_voices(self) -> list[str]:
        return self._tts.list_tts_voices()
