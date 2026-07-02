"""DI factory for speech engine."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from backend.infrastructure.speech.service import SpeechService


@dataclass
class SpeechContainer:
    service: SpeechService


def build_speech_container(models_root: Path) -> SpeechContainer:
    return SpeechContainer(service=SpeechService(models_root=models_root))
