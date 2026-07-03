"""ModeRouter: maps IntentLabel → BaseModality, respects feature flags."""
from __future__ import annotations

from backend.shared.logging import get_logger

from .modalities import (
    ClassificationModality,
    ConversationModality,
    DocumentAnalysisModality,
    ExtractionModality,
    LogAnalysisModality,
    NerModality,
    QaModality,
    RagModality,
    RewriteModality,
    SpeechModality,
    SummaryModality,
    TimeseriesModality,
    TranslationModality,
)
from .modalities.base import BaseModality, ICoreAI
from .models import IntentLabel, ModalityRequest, ModalityResponse

logger = get_logger(__name__)

# Default feature-flag mapping — all enabled
_DEFAULT_FLAGS: dict[IntentLabel, bool] = {
    IntentLabel.CLASSIFICATION:    True,
    IntentLabel.DOCUMENT_ANALYSIS: True,
    IntentLabel.EXTRACTION:        True,
    IntentLabel.NER:               True,
    IntentLabel.SUMMARY:           True,
    IntentLabel.TRANSLATION:       True,
    IntentLabel.REWRITE:           True,
    IntentLabel.QA:                True,
    IntentLabel.RAG:               True,
    IntentLabel.CONVERSATION:      True,
    IntentLabel.TIMESERIES:        True,
    IntentLabel.LOG_ANALYSIS:      True,
    IntentLabel.SPEECH:            True,
    IntentLabel.UNKNOWN:           False,
}


class ModeRouter:
    """
    Routes a ModalityRequest to the correct BaseModality.

    Feature flags can be toggled per-intent at construction time
    or at runtime via enable() / disable().
    """

    def __init__(
        self,
        feature_flags: dict[IntentLabel, bool] | None = None,
        knowledge_engine=None,
        speech_adapter=None,
    ) -> None:
        self._flags: dict[IntentLabel, bool] = {
            **_DEFAULT_FLAGS,
            **(feature_flags or {}),
        }
        # Build registry
        self._registry: dict[IntentLabel, BaseModality] = {
            IntentLabel.CLASSIFICATION:    ClassificationModality(),
            IntentLabel.DOCUMENT_ANALYSIS: DocumentAnalysisModality(),
            IntentLabel.EXTRACTION:        ExtractionModality(),
            IntentLabel.NER:               NerModality(),
            IntentLabel.SUMMARY:           SummaryModality(),
            IntentLabel.TRANSLATION:       TranslationModality(),
            IntentLabel.REWRITE:           RewriteModality(),
            IntentLabel.QA:                QaModality(),
            IntentLabel.RAG:               RagModality(knowledge_engine=knowledge_engine),
            IntentLabel.CONVERSATION:      ConversationModality(),
            IntentLabel.TIMESERIES:        TimeseriesModality(),
            IntentLabel.LOG_ANALYSIS:      LogAnalysisModality(),
            IntentLabel.SPEECH:            SpeechModality(speech_adapter=speech_adapter),
        }

    # ---------------------------------------------------------------- #
    # Feature flag management                                           #
    # ---------------------------------------------------------------- #

    def enable(self, intent: IntentLabel) -> None:
        self._flags[intent] = True

    def disable(self, intent: IntentLabel) -> None:
        self._flags[intent] = False

    def is_enabled(self, intent: IntentLabel) -> bool:
        return self._flags.get(intent, False)

    def enabled_intents(self) -> list[IntentLabel]:
        return [i for i, enabled in self._flags.items() if enabled]

    # ---------------------------------------------------------------- #
    # Routing                                                           #
    # ---------------------------------------------------------------- #

    async def route(
        self,
        request: ModalityRequest,
        core_ai: ICoreAI,
    ) -> ModalityResponse:
        """Dispatch *request* to the correct modality.

        Falls back to CONVERSATION if the intent is disabled or UNKNOWN.
        """
        intent = request.intent

        if not self._flags.get(intent, False):
            logger.warning("router.intent.disabled", intent=intent)
            fallback_req = request.model_copy(update={"intent": IntentLabel.CONVERSATION})
            modality = self._registry[IntentLabel.CONVERSATION]
            response = await modality.execute(fallback_req, core_ai)
            response.fallback_used = True
            response.metadata["original_intent"] = intent
            return response

        modality = self._registry.get(intent)
        if modality is None:
            logger.error("router.modality.missing", intent=intent)
            return ModalityResponse(
                session_id=request.session_id,
                intent=intent,
                result=None,
                fallback_used=True,
                error=f"No modality registered for intent: {intent}",
            )

        logger.info("router.dispatch", intent=intent, session_id=request.session_id)
        return await modality.execute(request, core_ai)
