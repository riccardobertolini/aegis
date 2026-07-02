"""Port: CoreAI Engine — top-level AI pipeline orchestrator."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class AIRequest:
    session_id: str
    user_input: str
    context: dict = field(default_factory=dict)


@dataclass
class AIResponse:
    session_id: str
    text: str
    engine_trace: list[str] = field(default_factory=list)  # which engines were invoked
    metadata: dict = field(default_factory=dict)


class ICoreAIPort(ABC):
    """Contract for the top-level AI request handler."""

    @abstractmethod
    async def process(self, request: AIRequest) -> AIResponse: ...
