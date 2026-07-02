"""Port: Translation Engine."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TranslationRequest:
    text: str
    source_lang: str  # ISO 639-1 e.g. "it"
    target_lang: str  # ISO 639-1 e.g. "en"
    metadata: dict = field(default_factory=dict)


@dataclass
class TranslationResult:
    text: str
    source_lang: str
    target_lang: str
    error: Optional[str] = None
    metadata: dict = field(default_factory=dict)


class ITranslationPort(ABC):
    """Contract for local offline translation."""

    @abstractmethod
    async def translate(self, request: TranslationRequest) -> TranslationResult: ...

    @abstractmethod
    async def list_language_pairs(self) -> list[tuple[str, str]]: ...
