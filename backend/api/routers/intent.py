"""REST endpoints for Intent Engine."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.infrastructure.adapters.intent.intent_classifier import IntentClassifier
from backend.infrastructure.adapters.intent.models import (
    IntentLabel,
    ModalityRequest,
    ModalityResponse,
)

router = APIRouter(prefix="/intent", tags=["intent"])
_classifier = IntentClassifier()


class ClassifyRequest(BaseModel):
    text: str


class ClassifyResponse(BaseModel):
    intent: str
    confidence: float
    ambiguous: bool
    fallback: bool
    top_candidates: list[tuple[str, float]]


@router.post("/classify", response_model=ClassifyResponse)
def classify(req: ClassifyRequest) -> ClassifyResponse:
    """Classify user text and return predicted intent."""
    pred = _classifier.classify(req.text)
    return ClassifyResponse(
        intent=pred.intent.value,
        confidence=round(pred.confidence, 4),
        ambiguous=pred.ambiguous,
        fallback=pred.fallback,
        top_candidates=pred.top_candidates,
    )


@router.get("/intents")
def list_intents() -> dict:
    """Return all known intent labels."""
    return {"intents": [i.value for i in IntentLabel if i != IntentLabel.UNKNOWN]}
