"""Port: Inference Engine."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator


@dataclass
class InferenceRequest:
    prompt: str
    model_id: str
    max_tokens: int = 512
    temperature: float = 0.7
    stream: bool = False
    extra: dict = field(default_factory=dict)


@dataclass
class InferenceResponse:
    text: str
    model_id: str
    prompt_tokens: int
    completion_tokens: int
    finish_reason: str  # "stop" | "length" | "error"


class IInferencePort(ABC):
    """Contract for local SSM inference."""

    @abstractmethod
    async def run(self, request: InferenceRequest) -> InferenceResponse:
        """Execute a single inference call."""
        ...

    @abstractmethod
    async def stream(self, request: InferenceRequest) -> AsyncIterator[str]:
        """Stream tokens for a given prompt."""
        ...

    @abstractmethod
    async def list_models(self) -> list[str]:
        """Return IDs of all locally available models."""
        ...

    @abstractmethod
    async def load_model(self, model_id: str) -> None:
        """Load a model into memory. No network calls allowed."""
        ...

    @abstractmethod
    async def unload_model(self, model_id: str) -> None:
        """Release a model from memory."""
        ...
