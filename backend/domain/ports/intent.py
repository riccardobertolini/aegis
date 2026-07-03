"""Port: Intent Engine."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum


class IntentMode(StrEnum):
    HEURISTIC = "heuristic"
    SSM = "ssm"
    HYBRID = "hybrid"


@dataclass
class IntentRequest:
    text: str
    session_id: str
    context: dict = field(default_factory=dict)


@dataclass
class IntentCandidate:
    intent: str
    score: float
    reason: str = ""


@dataclass
class IntentResult:
    intent: str          # e.g. "search_knowledge", "run_inference", "translate"
    confidence: float
    entities: dict = field(default_factory=dict)
    suggested_engine: str = ""
    mode: IntentMode = IntentMode.HYBRID
    candidates: list[IntentCandidate] = field(default_factory=list)
    needs_clarification: bool = False
    clarification_question: str | None = None


class IIntentPort(ABC):
    """Contract for intent classification."""

    @abstractmethod
    async def classify(self, request: IntentRequest) -> IntentResult: ...
