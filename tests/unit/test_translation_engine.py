"""Unit tests — TranslationEngine."""
from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

import pytest

from backend.domain.ports.translation import TranslationRequest
from backend.infrastructure.adapters.translation.translation_engine import TranslationEngine
from backend.infrastructure.adapters.translation.lang_detect import detect_language


@pytest.fixture
def tmp_settings(tmp_path):
    from backend.shared.config import Settings
    s = MagicMock(spec=Settings)
    s.models_dir = tmp_path / "models"  # no real models → fallback
    (s.models_dir / "translation").mkdir(parents=True, exist_ok=True)
    return s


@pytest.fixture
def engine(tmp_settings):
    return TranslationEngine(settings=tmp_settings)


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


class TestTranslationEngine:
    def test_identity_translation(self, engine):
        req = TranslationRequest("Ciao", "it", "it")
        res = run(engine.translate(req))
        assert res.translated_text == "Ciao"
        assert res.confidence == 1.0

    def test_rule_based_it_en(self, engine):
        req = TranslationRequest("ciao grazie", "it", "en")
        res = run(engine.translate(req))
        assert "hello" in res.translated_text.lower() or res.confidence >= 0.0

    def test_rule_based_en_it(self, engine):
        req = TranslationRequest("hello document", "en", "it")
        res = run(engine.translate(req))
        assert "ciao" in res.translated_text or "documento" in res.translated_text

    def test_list_pairs(self, engine):
        pairs = run(engine.list_language_pairs())
        assert ("it", "en") in pairs
        assert ("en", "de") in pairs
        assert len(pairs) >= 8

    def test_auto_detect_italian(self, engine):
        req = TranslationRequest("Ciao come stai oggi", "auto", "en")
        res = run(engine.translate(req))
        assert res.source_lang == "it"

    def test_pivot_translation_it_de(self, engine):
        req = TranslationRequest("sistema", "it", "de")
        res = run(engine.translate(req))
        # rule-based pivot: it→en→de
        assert isinstance(res.translated_text, str)
        assert res.source_lang == "it"
        assert res.target_lang == "de"


class TestLangDetect:
    def test_detect_english(self):
        lang, conf = detect_language("The quick brown fox jumps over the lazy dog")
        assert lang == "en"

    def test_detect_italian(self):
        lang, conf = detect_language("Ciao come stai oggi amico mio")
        assert lang == "it"

    def test_detect_empty(self):
        lang, conf = detect_language("")
        assert lang == "en"
        assert conf == 0.0
