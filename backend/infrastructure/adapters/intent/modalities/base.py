"""Abstract base class for all modalities."""
from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable

from ..models import IntentLabel, ModalityRequest, ModalityResponse


@runtime_checkable
class ICoreAI(Protocol):
    """Minimal interface expected from CoreAI — duck-typed for testability."""
    async def generate(self, prompt: str, **kwargs) -> str: ...


class BaseModality(ABC):
    """Every modality implements this contract."""

    @property
    @abstractmethod
    def intent(self) -> IntentLabel:
        """The intent this modality handles."""
        ...

    @abstractmethod
    async def execute(
        self,
        request: ModalityRequest,
        core_ai: ICoreAI,
    ) -> ModalityResponse:
        """Run the modality and return a ModalityResponse."""
        ...

    # ---------------------------------------------------------------- #
    # Helper: build a fallback response                                 #
    # ---------------------------------------------------------------- #
    def fallback_response(
        self,
        request: ModalityRequest,
        reason: str,
    ) -> ModalityResponse:
        return ModalityResponse(
            session_id=request.session_id,
            intent=request.intent,
            result=None,
            confidence=0.0,
            fallback_used=True,
            error=reason,
        )
