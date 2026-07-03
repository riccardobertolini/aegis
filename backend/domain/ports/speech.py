"""Port: Speech Engine (STT / TTS — offline only)."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class TranscriptionRequest:
    audio_bytes: bytes
    language: str = "it"       # ISO 639-1
    model_id: str = "default"  # maps to a local Whisper model variant


@dataclass
class TranscriptionResult:
    text: str
    language: str
    confidence: float
    segments: list[dict] = field(default_factory=list)  # [{start, end, text}]
    error: str | None = None


@dataclass
class SynthesisRequest:
    text: str
    language: str = "it"
    voice_id: str = "default"
    speed: float = 1.0   # 0.5 – 2.0
    pitch: float = 1.0   # 0.5 – 2.0


@dataclass
class SynthesisResult:
    audio_bytes: bytes
    sample_rate: int
    encoding: str        # "wav" | "ogg"
    duration_s: float = 0.0
    error: str | None = None


class ISpeechPort(ABC):
    """Contract for fully offline STT / TTS."""

    @abstractmethod
    async def transcribe(self, request: TranscriptionRequest) -> TranscriptionResult: ...

    @abstractmethod
    async def synthesize(self, request: SynthesisRequest) -> SynthesisResult: ...

    @abstractmethod
    async def list_stt_models(self) -> list[str]: ...

    @abstractmethod
    async def list_tts_voices(self) -> list[str]: ...
