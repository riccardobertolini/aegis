"""Intent service — hybrid heuristic + SSM classification."""
from __future__ import annotations

from backend.domain.ports.intent import (
    IIntentPort,
    IntentCandidate,
    IntentMode,
    IntentRequest,
    IntentResult,
)
from backend.domain.ports.knowledge import IKnowledgePort, SearchQuery
from backend.infrastructure.intent.rules import HeuristicIntentClassifier
from backend.infrastructure.intent.ssm_classifier import SSMIntentClassifier


class IntentService(IIntentPort):
    """
    Hybrid pipeline:
    1. Heuristic classification for deterministic offline routing.
    2. Optional SSM refinement using the existing local Mamba inference engine.
    3. Optional knowledge peek to enrich entities / raise confidence.
    """

    def __init__(
        self,
        heuristic: HeuristicIntentClassifier,
        ssm: SSMIntentClassifier | None = None,
        knowledge: IKnowledgePort | None = None,
        clarification_threshold: float = 0.55,
    ):
        self._heuristic = heuristic
        self._ssm = ssm
        self._knowledge = knowledge
        self._clarification_threshold = clarification_threshold

    async def classify(self, request: IntentRequest) -> IntentResult:
        intent, confidence, entities, suggested_engine, candidates = self._heuristic.classify(request.text)
        mode = IntentMode.HEURISTIC

        if self._ssm is not None:
            try:
                ssm_result = await self._ssm.classify(request.text, request.context)
                intent = ssm_result["intent"] or intent
                confidence = max(confidence, float(ssm_result.get("confidence", confidence)))
                entities = {**entities, **(ssm_result.get("entities") or {})}
                suggested_engine = ssm_result.get("suggested_engine") or suggested_engine
                mode = IntentMode.HYBRID
            except Exception:
                mode = IntentMode.HEURISTIC

        if self._knowledge is not None and intent in {"search_knowledge", "question_answering"}:
            try:
                peek = await self._knowledge.search(SearchQuery(text=request.text, top_k=1))
                if peek:
                    confidence = min(0.99, confidence + 0.1)
                    entities.setdefault("knowledge_hit", True)
                    entities.setdefault("top_document_id", peek[0].document.id)
            except Exception:
                pass

        ranked_candidates = [
            IntentCandidate(intent=name, score=score, reason=reason)
            for name, score, reason in candidates
        ]

        needs_clarification = confidence < self._clarification_threshold
        clarification_question = None
        if needs_clarification:
            clarification_question = self._build_clarification_question(ranked_candidates)

        return IntentResult(
            intent=intent,
            confidence=round(confidence, 4),
            entities=entities,
            suggested_engine=suggested_engine,
            mode=mode,
            candidates=ranked_candidates,
            needs_clarification=needs_clarification,
            clarification_question=clarification_question,
        )

    @staticmethod
    def _build_clarification_question(candidates: list[IntentCandidate]) -> str:
        top = ", ".join(candidate.intent for candidate in candidates[:3]) or "run_inference"
        return (
            "Richiesta ambigua. Confermi se vuoi: "
            f"{top}?"
        )
