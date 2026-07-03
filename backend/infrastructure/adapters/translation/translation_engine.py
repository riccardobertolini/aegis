"""TranslationEngine — offline NMT / rule-based translation.

Implements ITranslationPort.

Strategy (layered, all offline):
1. Helsinki-NLP OPUS-MT models via ``ctranslate2`` or ``transformers``
   (models must be pre-downloaded into models/translation/).
2. If model files are absent: rule-based word-substitution fallback
   (useful for smoke-tests / air-gap environments without pre-loaded models).

Supported pairs (extend by adding model dirs):
  IT↔EN, EN↔IT, EN↔DE, DE↔EN, EN↔FR, FR↔EN, IT→DE, IT→FR, DE↔FR

Auto-detect source language when source_lang == "auto".
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.domain.ports.translation import (
    ITranslationPort,
    TranslationRequest,
    TranslationResult,
)
from backend.infrastructure.adapters.translation.lang_detect import detect_language
from backend.shared.config import Settings, get_settings
from backend.shared.logging import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Supported language pairs
# ---------------------------------------------------------------------------

_PAIRS: list[tuple[str, str]] = [
    ("it", "en"), ("en", "it"),
    ("en", "de"), ("de", "en"),
    ("en", "fr"), ("fr", "en"),
    ("it", "de"), ("de", "it"),
    ("it", "fr"), ("fr", "it"),
    ("de", "fr"), ("fr", "de"),
]

# Helsinki-NLP model naming convention
_MODEL_NAME: dict[tuple[str, str], str] = {
    ("it", "en"): "opus-mt-it-en",
    ("en", "it"): "opus-mt-en-it",
    ("en", "de"): "opus-mt-en-de",
    ("de", "en"): "opus-mt-de-en",
    ("en", "fr"): "opus-mt-en-fr",
    ("fr", "en"): "opus-mt-fr-en",
    ("it", "de"): "opus-mt-it-de",
    ("de", "it"): "opus-mt-de-it",
    ("it", "fr"): "opus-mt-it-fr",
    ("fr", "it"): "opus-mt-fr-it",
    ("de", "fr"): "opus-mt-de-fr",
    ("fr", "de"): "opus-mt-fr-de",
}

# ---------------------------------------------------------------------------
# Rule-based fallback dictionary (minimal — for smoke-tests only)
# ---------------------------------------------------------------------------

_FALLBACK_DICT: dict[tuple[str, str], dict[str, str]] = {
    ("it", "en"): {
        "ciao": "hello", "grazie": "thank you", "documento": "document",
        "analisi": "analysis", "sistema": "system", "errore": "error",
        "risposta": "answer", "domanda": "question", "file": "file",
    },
    ("en", "it"): {
        "hello": "ciao", "thank you": "grazie", "document": "documento",
        "analysis": "analisi", "system": "sistema", "error": "errore",
        "answer": "risposta", "question": "domanda",
    },
    ("en", "de"): {
        "hello": "hallo", "document": "Dokument", "analysis": "Analyse",
        "system": "System", "error": "Fehler", "answer": "Antwort",
    },
    ("en", "fr"): {
        "hello": "bonjour", "document": "document", "analysis": "analyse",
        "system": "système", "error": "erreur", "answer": "réponse",
    },
}


class TranslationEngine(ITranslationPort):
    """Offline translation engine."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._models_dir = self._settings.models_dir / "translation"
        self._model_cache: dict[tuple[str, str], Any] = {}

    # ------------------------------------------------------------------
    # ITranslationPort
    # ------------------------------------------------------------------

    async def translate(self, request: TranslationRequest) -> TranslationResult:
        src = request.source_lang
        tgt = request.target_lang

        # Auto-detect
        detected_conf = 1.0
        if src == "auto":
            src, detected_conf = detect_language(request.text)
            logger.debug("translation.detect", detected=src, conf=detected_conf)

        src = src.lower()
        tgt = tgt.lower()

        # Same language → identity
        if src == tgt:
            return TranslationResult(
                translated_text=request.text,
                source_lang=src,
                target_lang=tgt,
                confidence=1.0,
            )

        # Pivot via English if direct pair unavailable
        if (src, tgt) not in _MODEL_NAME:
            if (src, "en") in _MODEL_NAME and ("en", tgt) in _MODEL_NAME:
                pivot_req = TranslationRequest(request.text, src, "en")
                pivot_res = await self.translate(pivot_req)
                final_req = TranslationRequest(pivot_res.translated_text, "en", tgt)
                final_res = await self.translate(final_req)
                return TranslationResult(
                    translated_text=final_res.translated_text,
                    source_lang=src,
                    target_lang=tgt,
                    confidence=round(pivot_res.confidence * final_res.confidence, 3),
                )

        translated, confidence = self._run_model(src, tgt, request.text)
        return TranslationResult(
            translated_text=translated,
            source_lang=src,
            target_lang=tgt,
            confidence=round(confidence * detected_conf, 3),
        )

    async def list_language_pairs(self) -> list[tuple[str, str]]:
        return list(_PAIRS)

    # ------------------------------------------------------------------
    # Internal model dispatch
    # ------------------------------------------------------------------

    def _run_model(self, src: str, tgt: str, text: str) -> tuple[str, float]:
        pair = (src, tgt)
        model_name = _MODEL_NAME.get(pair)

        if model_name:
            model_path = self._models_dir / model_name
            if model_path.exists():
                return self._run_ctranslate2(model_path, text)

        # Rule-based fallback
        logger.warning(
            "translation.fallback",
            pair=f"{src}->{tgt}",
            reason="model_not_found",
        )
        return self._rule_based(src, tgt, text)

    def _run_ctranslate2(
        self, model_path: Path, text: str
    ) -> tuple[str, float]:
        """Use CTranslate2 for efficient local inference."""
        try:
            import ctranslate2  # type: ignore
            import sentencepiece as spm  # type: ignore

            sp = spm.SentencePieceProcessor()
            sp.Load(str(model_path / "source.spm"))

            if (model_path / "source.spm") not in self._model_cache:
                translator = ctranslate2.Translator(
                    str(model_path), inter_threads=1, intra_threads=2
                )
                self._model_cache[model_path] = (translator, sp)

            translator, sp = self._model_cache[model_path]
            tokens = sp.Encode(text, out_type=str)
            results = translator.translate_batch([tokens])
            target_tokens = results[0].hypotheses[0]

            sp_tgt = spm.SentencePieceProcessor()
            sp_tgt.Load(str(model_path / "target.spm"))
            translated = sp_tgt.Decode(target_tokens)
            return translated, 0.88
        except Exception as exc:
            logger.error("translation.ctranslate2_error", error=str(exc))
            return text, 0.0

    def _rule_based(self, src: str, tgt: str, text: str) -> tuple[str, float]:
        """Token-level word substitution (smoke-test / offline fallback)."""
        lookup = _FALLBACK_DICT.get((src, tgt), {})
        if not lookup:
            return text, 0.0
        words = text.split()
        translated = [lookup.get(w.lower(), w) for w in words]
        return " ".join(translated), 0.35
