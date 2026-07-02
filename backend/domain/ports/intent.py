"""Port: Intent Engine."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class IntentRequest:
    text: str
    session_id: str
    context: dict = field(default_factory=dict)


@dataclass
class IntentResult:
    intent: str          # e.g. "search_knowledge", "run_inference", "translate"
    confidence: float
    entities: dict = field(default_factory=dict)
    suggested_engine: str = ""


class IIntentPort(ABC):
    """Contract for intent classification."""

    @abstractmethod
    async def classify(self, request: IntentRequest) -> IntentResult: ...
