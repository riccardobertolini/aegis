"""Intent API router."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.domain.ports.intent import IntentRequest

router = APIRouter(prefix="/api/v1/intent", tags=["intent"])


def _get_intent_service():
    raise HTTPException(status_code=503, detail="IntentService not initialised")


class IntentClassifyRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=4096)
    session_id: str = Field(..., min_length=1, max_length=256)
    context: dict = Field(default_factory=dict)


class IntentCandidateOut(BaseModel):
    intent: str
    score: float
    reason: str = ""


class IntentClassifyResponse(BaseModel):
    intent: str
    confidence: float
    entities: dict
    suggested_engine: str
    mode: str
    candidates: list[IntentCandidateOut]
    needs_clarification: bool
    clarification_question: str | None


@router.post("/classify", response_model=IntentClassifyResponse)
async def classify_intent(
    req: IntentClassifyRequest,
    service=Depends(_get_intent_service),
):
    result = await service.classify(
        IntentRequest(text=req.text, session_id=req.session_id, context=req.context)
    )
    return IntentClassifyResponse(
        intent=result.intent,
        confidence=result.confidence,
        entities=result.entities,
        suggested_engine=result.suggested_engine,
        mode=result.mode.value,
        candidates=[
            IntentCandidateOut(intent=c.intent, score=c.score, reason=c.reason)
            for c in result.candidates
        ],
        needs_clarification=result.needs_clarification,
        clarification_question=result.clarification_question,
    )
