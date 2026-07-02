"""STT service using faster-whisper (offline, local model files)."""
from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Optional

from backend.domain.ports.speech import (
    ISpeechPort,
    TranscriptionRequest,
    TranscriptionResult,
    SynthesisRequest,
    SynthesisResult,
)

logger = logging.getLogger(__name__)


class WhisperSTTService:
    """
    Speech-to-Text using faster-whisper (CTranslate2 backend).
    Models must be pre-downloaded into models_root/<model_id>/.
    NO network calls: local_files_only is always True.

    Install:
        pip install faster-whisper
    Pre-download model (internet machine):
        huggingface-cli download Systran/faster-whisper-small --local-dir models/faster-whisper-small
    """

    def __init__(self, models_root: Path, default_model_id: str = "faster-whisper-small"):
        self._models_root = models_root
        self._default_model_id = default_model_id
        self._models: dict[str, object] = {}

    def _get_model(self, model_id: str):
        if model_id in self._models:
            return self._models[model_id]
        try:
            from faster_whisper import WhisperModel  # type: ignore
        except ImportError:
            raise RuntimeError(
                "faster-whisper not installed. Run: pip install faster-whisper"
            )
        model_path = self._models_root / model_id
        if not model_path.exists():
            raise FileNotFoundError(
                f"Whisper model '{model_id}' not found at {model_path}. "
                "Download it with: huggingface-cli download Systran/faster-whisper-small "
                f"--local-dir {model_path}"
            )
        logger.info("Loading Whisper model: %s", model_path)
        model = WhisperModel(
            str(model_path),
            device="cpu",
            compute_type="int8",
            local_files_only=True,  # NEVER reach out to network
        )
        self._models[model_id] = model
        return model

    async def transcribe(self, request: TranscriptionRequest) -> TranscriptionResult:
        model_id = request.model_id if request.model_id != "default" else self._default_model_id
        try:
            model = self._get_model(model_id)
            audio_io = io.BytesIO(request.audio_bytes)
            segments, info = model.transcribe(
                audio_io,
                language=request.language if request.language != "auto" else None,
                beam_size=5,
            )
            seg_list = list(segments)
            full_text = " ".join(s.text.strip() for s in seg_list)
            return TranscriptionResult(
                text=full_text,
                language=info.language,
                confidence=float(info.language_probability),
                segments=[
                    {"start": s.start, "end": s.end, "text": s.text}
                    for s in seg_list
                ],
            )
        except Exception as exc:
            logger.error("STT error: %s", exc)
            return TranscriptionResult(
                text="", language=request.language, confidence=0.0, error=str(exc)
            )

    def list_stt_models(self) -> list[str]:
        if not self._models_root.exists():
            return []
        return [
            d.name for d in self._models_root.iterdir()
            if d.is_dir() and (d / "model.bin").exists()
        ]
