"""TTS service: Coqui TTS (offline) with pyttsx3 fallback."""
from __future__ import annotations

import io
import logging
from pathlib import Path

from backend.domain.ports.speech import SynthesisRequest, SynthesisResult

logger = logging.getLogger(__name__)


class CoquiTTSService:
    """
    Text-to-Speech using Coqui TTS (offline, local model directory).
    Falls back to pyttsx3 (system TTS, always available) if Coqui not installed.

    Install Coqui:
        pip install TTS
    Pre-download model (internet machine):
        tts --model_name tts_models/it/mai_female/glow-tts --list_models
        # then copy ~/.local/share/tts/ to air-gapped machine

    Install pyttsx3 fallback:
        pip install pyttsx3
    """

    def __init__(self, models_root: Path, default_voice: str = "default"):
        self._models_root = models_root
        self._default_voice = default_voice
        self._coqui_model = None
        self._pyttsx3_engine = None

    def _get_coqui(self):
        if self._coqui_model is not None:
            return self._coqui_model
        try:
            from TTS.api import TTS  # type: ignore
            model_path = self._models_root / "coqui-tts"
            if model_path.exists():
                self._coqui_model = TTS(model_path=str(model_path), progress_bar=False)
            else:
                # Use any first available local model dir
                candidates = [d for d in self._models_root.iterdir() if d.is_dir()]
                if candidates:
                    self._coqui_model = TTS(model_path=str(candidates[0]), progress_bar=False)
            return self._coqui_model
        except ImportError:
            return None

    def _get_pyttsx3(self):
        if self._pyttsx3_engine is not None:
            return self._pyttsx3_engine
        try:
            import pyttsx3  # type: ignore
            engine = pyttsx3.init()
            self._pyttsx3_engine = engine
            return engine
        except Exception:
            return None

    async def synthesize(self, request: SynthesisRequest) -> SynthesisResult:
        # Try Coqui first
        coqui = self._get_coqui()
        if coqui is not None:
            return await self._synthesize_coqui(coqui, request)
        # Fall back to pyttsx3
        engine = self._get_pyttsx3()
        if engine is not None:
            return self._synthesize_pyttsx3(engine, request)
        return SynthesisResult(
            audio_bytes=b"",
            sample_rate=22050,
            encoding="wav",
            error="No TTS engine available. Install 'TTS' (Coqui) or 'pyttsx3'.",
        )

    async def _synthesize_coqui(
        self, model, request: SynthesisRequest
    ) -> SynthesisResult:
        try:
            import numpy as np  # type: ignore
            import soundfile as sf  # type: ignore
            wav = model.tts(text=request.text, speed=request.speed)
            buf = io.BytesIO()
            sf.write(buf, np.array(wav), 22050, format="WAV")
            audio_bytes = buf.getvalue()
            duration = len(wav) / 22050
            return SynthesisResult(
                audio_bytes=audio_bytes,
                sample_rate=22050,
                encoding="wav",
                duration_s=round(duration, 2),
            )
        except Exception as exc:
            logger.error("Coqui TTS error: %s", exc)
            return SynthesisResult(
                audio_bytes=b"", sample_rate=22050, encoding="wav", error=str(exc)
            )

    def _synthesize_pyttsx3(
        self, engine, request: SynthesisRequest
    ) -> SynthesisResult:
        try:
            import os
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name
            engine.setProperty("rate", int(150 * request.speed))
            engine.save_to_file(request.text, tmp_path)
            engine.runAndWait()
            with open(tmp_path, "rb") as f:
                audio_bytes = f.read()
            os.unlink(tmp_path)
            return SynthesisResult(
                audio_bytes=audio_bytes,
                sample_rate=22050,
                encoding="wav",
            )
        except Exception as exc:
            logger.error("pyttsx3 TTS error: %s", exc)
            return SynthesisResult(
                audio_bytes=b"", sample_rate=22050, encoding="wav", error=str(exc)
            )

    def list_tts_voices(self) -> list[str]:
        engine = self._get_pyttsx3()
        if engine:
            try:
                return [v.id for v in engine.getProperty("voices")]
            except Exception:
                pass
        return ["default"]
