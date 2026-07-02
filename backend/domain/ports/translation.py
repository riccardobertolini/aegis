"""Port: Translation Engine (offline NMT)."""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class TranslationRequest:
    text: str
    source_lang: str  # ISO 639-1, or "auto"
    target_lang: str


@dataclass
class TranslationResult:
    translated_text: str
    source_lang: str
    target_lang: str
    confidence: float


class ITranslationPort(ABC):
    """Contract for fully offline neural machine translation."""

    @abstractmethod
    async def translate(self, request: TranslationRequest) -> TranslationResult: ...

    @abstractmethod
    async def list_language_pairs(self) -> list[tuple[str, str]]: ...
