"""Unit tests for heuristic intent rules."""
from backend.infrastructure.intent.rules import HeuristicIntentClassifier


def test_search_knowledge_intent_detected():
    classifier = HeuristicIntentClassifier()
    intent, confidence, entities, engine, candidates = classifier.classify(
        "Cerca nel knowledge base il manuale utente top 3"
    )
    assert intent == "search_knowledge"
    assert confidence > 0.3
    assert entities["top_k"] == 3
    assert engine == "knowledge"
    assert candidates


def test_run_inference_detected_with_entities():
    classifier = HeuristicIntentClassifier()
    intent, confidence, entities, engine, _ = classifier.classify(
        "Genera una completion model_id:mamba-chat temperature:0.2 max_tokens:128"
    )
    assert intent == "run_inference"
    assert entities["model_id"] == "mamba-chat"
    assert entities["temperature"] == 0.2
    assert entities["max_tokens"] == 128
    assert engine == "inference"


def test_fallback_to_run_inference_for_unknown_text():
    classifier = HeuristicIntentClassifier()
    intent, confidence, entities, engine, _ = classifier.classify("ciao")
    assert intent == "run_inference"
    assert confidence == 0.25
    assert entities == {}
    assert engine == "inference"
