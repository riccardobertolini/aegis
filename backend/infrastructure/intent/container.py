"""Dependency injection for intent engine."""
from __future__ import annotations

from dataclasses import dataclass

from backend.domain.ports.inference import IInferencePort
from backend.domain.ports.knowledge import IKnowledgePort
from backend.infrastructure.intent.rules import HeuristicIntentClassifier
from backend.infrastructure.intent.service import IntentService
from backend.infrastructure.intent.ssm_classifier import SSMIntentClassifier


@dataclass
class IntentContainer:
    service: IntentService
    heuristic: HeuristicIntentClassifier
    ssm: SSMIntentClassifier | None = None


def build_intent_container(
    inference: IInferencePort,
    knowledge: IKnowledgePort | None = None,
    model_id: str | None = None,
) -> IntentContainer:
    heuristic = HeuristicIntentClassifier()
    ssm = SSMIntentClassifier(inference=inference, model_id=model_id)
    service = IntentService(
        heuristic=heuristic,
        ssm=ssm,
        knowledge=knowledge,
    )
    return IntentContainer(service=service, heuristic=heuristic, ssm=ssm)
