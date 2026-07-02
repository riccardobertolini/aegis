"""IntentEngine: unified façade — classify → route → respond.

Implements IIntentPort.
"""
from __future__ import annotations

from backend.domain.ports.intent import IIntentPort, IntentRequest, IntentResult
from backend.shared.logging import get_logger

from .intent_classifier import IntentClassifier
from .mode_router import ModeRouter
from .models import IntentLabel, ModalityRequest, ModalityResponse

logger = get_logger(__name__)


class IntentEngine(IIntentPort):
    """
    Combines IntentClassifier + ModeRouter into a single entry-point.

    Usage:
        engine = IntentEngine(core_ai=my_core_ai)
        response = await engine.run(session_id, user_text, kb_ids=[...])
    """

    def __init__(
        self,
        core_ai=None,
        knowledge_engine=None,
        speech_adapter=None,
        feature_flags: dict[IntentLabel, bool] | None = None,
        confidence_threshold: float = 0.05,
        ambiguity_margin: float = 0.02,
    ) -> None:
        self._core_ai   = core_ai
        self._classifier = IntentClassifier(
            confidence_threshold=confidence_threshold,
            ambiguity_margin=ambiguity_margin,
        )
        self._router = ModeRouter(
            feature_flags=feature_flags,
            knowledge_engine=knowledge_engine,
            speech_adapter=speech_adapter,
        )

    # ---------------------------------------------------------------- #
    # IIntentPort                                                        #
    # ---------------------------------------------------------------- #

    async def classify(self, request: IntentRequest) -> IntentResult:
        """Classify only — does not execute any modality."""
        prediction = self._classifier.classify(request.text)
        return IntentResult(
            intent=prediction.intent.value,
            confidence=prediction.confidence,
            entities={},
            suggested_engine=prediction.intent.value,
        )

    # ---------------------------------------------------------------- #
    # Extended API                                                       #
    # ---------------------------------------------------------------- #

    async def run(
        self,
        session_id: str,
        text: str,
        documents: list[str] | None = None,
        kb_ids: list[str] | None = None,
        parameters: dict | None = None,
        context: dict | None = None,
        force_intent: IntentLabel | None = None,
    ) -> ModalityResponse:
        """Classify text → route to modality → return ModalityResponse."""
        if force_intent:
            intent = force_intent
        else:
            prediction = self._classifier.classify(text)
            intent     = prediction.intent
            logger.info(
                "intent_engine.run",
                session_id=session_id,
                intent=intent,
                confidence=round(prediction.confidence, 4),
                ambiguous=prediction.ambiguous,
            )

        req = ModalityRequest(
            session_id=session_id,
            intent=intent,
            text=text,
            documents=documents or [],
            kb_ids=kb_ids or [],
            parameters=parameters or {},
            context=context or {},
        )
        return await self._router.route(req, self._core_ai)

    # ---------------------------------------------------------------- #
    # Runtime feature flag control                                       #
    # ---------------------------------------------------------------- #

    def enable_modality(self, intent: IntentLabel) -> None:
        self._router.enable(intent)

    def disable_modality(self, intent: IntentLabel) -> None:
        self._router.disable(intent)

    def enabled_modalities(self) -> list[IntentLabel]:
        return self._router.enabled_intents()
