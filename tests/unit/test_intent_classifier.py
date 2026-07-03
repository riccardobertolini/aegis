"""Unit tests for IntentClassifier (offline TF-IDF)."""
import pytest

from backend.infrastructure.adapters.intent.intent_classifier import IntentClassifier
from backend.infrastructure.adapters.intent.models import IntentLabel


@pytest.fixture
def clf():
    return IntentClassifier(confidence_threshold=0.01, ambiguity_margin=0.02)


# ------------------------------------------------------------------ #
# Basic classification                                                 #
# ------------------------------------------------------------------ #

@pytest.mark.parametrize(("text", "expected"), [
    ("summarize this document",         IntentLabel.SUMMARY),
    ("translate to italian",            IntentLabel.TRANSLATION),
    ("find named entities in the text", IntentLabel.NER),
    ("analyze the logs for errors",     IntentLabel.LOG_ANALYSIS),
    ("search the knowledge base",       IntentLabel.RAG),
    ("transcribe audio file",           IntentLabel.SPEECH),
    ("hello how are you",               IntentLabel.CONVERSATION),
    ("classify this text category",     IntentLabel.CLASSIFICATION),
    ("rewrite this paragraph formally", IntentLabel.REWRITE),
    ("extract data from the table",     IntentLabel.EXTRACTION),
    ("analyze the time series data",    IntentLabel.TIMESERIES),
    ("answer my question about",        IntentLabel.QA),
])
def test_classify_known_intents(clf, text, expected):
    result = clf.classify(text)
    assert result.intent == expected, (
        f"Text: {text!r} → got {result.intent}, expected {expected}"
    )


def test_classify_returns_prediction_object(clf):
    pred = clf.classify("summarize this")
    assert pred.confidence > 0
    assert len(pred.top_candidates) >= 1


def test_fallback_on_empty_text(clf):
    pred = clf.classify("")
    assert pred.fallback is True or pred.intent == IntentLabel.UNKNOWN


def test_ambiguity_flag(clf):
    # Very short generic text may trigger ambiguity
    pred = clf.classify("help")
    # Should not raise; ambiguous may or may not be True
    assert isinstance(pred.ambiguous, bool)


def test_add_examples_updates_corpus(clf):
    clf.add_examples(IntentLabel.SUMMARY, ["give me a condensed version please"])
    pred = clf.classify("give me a condensed version please")
    assert pred.intent == IntentLabel.SUMMARY


def test_confidence_threshold_triggers_fallback():
    clf = IntentClassifier(confidence_threshold=999.0)  # impossibly high
    pred = clf.classify("summarize this")
    assert pred.fallback is True
    assert pred.intent == IntentLabel.UNKNOWN
