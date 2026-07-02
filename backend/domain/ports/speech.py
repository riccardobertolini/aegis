"""Port: Speech Engine (STT / TTS — offline)."""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class TranscriptionRequest:
    audio_bytes: bytes
    language: str = "it"  # ISO 639-1


@dataclass
class TranscriptionResult:
    text: str
    language: str
    confidence: float


@dataclass
class SynthesisRequest:
    text: str
    language: str = "it"
    voice_id: str = "default"


@dataclass
class SynthesisResult:
    audio_bytes: bytes
    sample_rate: int
    encoding: str  # "wav" | "ogg" | "mp3"


class ISpeechPort(ABC):
    """Contract for offline STT / TTS."""

    @abstractmethod
    async def transcribe(self, request: TranscriptionRequest) -> TranscriptionResult: ...

    @abstractmethod
    async def synthesize(self, request: SynthesisRequest) -> SynthesisResult: ...
