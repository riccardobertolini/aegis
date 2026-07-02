"""Unit tests — SpeechService (mocked backends)."""
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.domain.ports.speech import (
    SynthesisRequest,
    TranscriptionRequest,
    TranscriptionResult,
    SynthesisResult,
)


@pytest.mark.asyncio
async def test_transcribe_returns_result(tmp_path):
    from backend.infrastructure.speech.stt import WhisperSTTService

    svc = WhisperSTTService(models_root=tmp_path / "whisper")
    # Patch _get_model to return a mock
    mock_model = MagicMock()
    mock_segment = MagicMock()
    mock_segment.text = "Ciao mondo"
    mock_segment.start = 0.0
    mock_segment.end = 1.2
    mock_info = MagicMock()
    mock_info.language = "it"
    mock_info.language_probability = 0.99
    mock_model.transcribe.return_value = ([mock_segment], mock_info)
    svc._models["default"] = mock_model
    svc._default_model_id = "default"

    req = TranscriptionRequest(audio_bytes=b"fake_audio", language="it", model_id="default")
    result = await svc.transcribe(req)
    assert result.text == "Ciao mondo"
    assert result.language == "it"
    assert result.confidence == pytest.approx(0.99)


@pytest.mark.asyncio
async def test_synthesize_no_engine_returns_error(tmp_path):
    from backend.infrastructure.speech.tts import CoquiTTSService
    svc = CoquiTTSService(models_root=tmp_path / "tts")
    # Patch both engines to None
    svc._coqui_model = None
    svc._pyttsx3_engine = None
    with patch.object(svc, "_get_coqui", return_value=None), \
         patch.object(svc, "_get_pyttsx3", return_value=None):
        req = SynthesisRequest(text="Ciao", language="it")
        result = await svc.synthesize(req)
    assert result.error is not None
    assert result.audio_bytes == b""


def test_list_stt_models_empty_when_no_models(tmp_path):
    from backend.infrastructure.speech.stt import WhisperSTTService
    svc = WhisperSTTService(models_root=tmp_path / "whisper")
    assert svc.list_stt_models() == []
