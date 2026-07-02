"""Speech Engine REST API (STT + TTS)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/speech", tags=["speech"])


def _get_speech_service():
    raise HTTPException(status_code=503, detail="SpeechService not initialised")


class SynthesisIn(BaseModel):
    text: str = Field(..., min_length=1, max_length=4096)
    language: str = Field("it")
    voice_id: str = Field("default")
    speed: float = Field(1.0, ge=0.5, le=2.0)
    pitch: float = Field(1.0, ge=0.5, le=2.0)


@router.post("/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    language: str = Query("it"),
    model_id: str = Query("default"),
    svc=Depends(_get_speech_service),
):
    """Upload a WAV/OGG audio file and receive the transcript."""
    from backend.domain.ports.speech import TranscriptionRequest
    audio_bytes = await file.read()
    if len(audio_bytes) > 25 * 1024 * 1024:  # 25 MB cap
        raise HTTPException(status_code=413, detail="Audio file too large (max 25 MB)")
    req = TranscriptionRequest(
        audio_bytes=audio_bytes, language=language, model_id=model_id
    )
    result = await svc.transcribe(req)
    return {
        "text": result.text,
        "language": result.language,
        "confidence": result.confidence,
        "segments": result.segments,
        "error": result.error,
    }


@router.post("/synthesize", response_class=Response)
async def synthesize(
    body: SynthesisIn,
    svc=Depends(_get_speech_service),
):
    """Synthesize text to WAV audio bytes."""
    from backend.domain.ports.speech import SynthesisRequest
    req = SynthesisRequest(
        text=body.text,
        language=body.language,
        voice_id=body.voice_id,
        speed=body.speed,
        pitch=body.pitch,
    )
    result = await svc.synthesize(req)
    if result.error:
        raise HTTPException(status_code=500, detail=result.error)
    return Response(
        content=result.audio_bytes,
        media_type="audio/wav",
        headers={"X-Duration-Seconds": str(result.duration_s)},
    )


@router.get("/models/stt", response_model=list[str])
async def list_stt_models(svc=Depends(_get_speech_service)):
    return await svc.list_stt_models()


@router.get("/voices/tts", response_model=list[str])
async def list_tts_voices(svc=Depends(_get_speech_service)):
    return await svc.list_tts_voices()
