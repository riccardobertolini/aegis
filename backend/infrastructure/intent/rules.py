"""Rule-based local intent detection — zero dependencies, zero network."""
from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class IntentRule:
    intent: str
    patterns: list[str] = field(default_factory=list)
    suggested_engine: str = ""
    entity_extractors: dict[str, str] = field(default_factory=dict)


DEFAULT_INTENT_RULES: list[IntentRule] = [
    IntentRule(
        intent="search_knowledge",
        suggested_engine="knowledge",
        patterns=[
            r"\b(cerca|trova|search|find|lookup|rag|documento|documenti|knowledge|manuale|wiki)\b",
            r"\b(cosa dice|what does|where is|in quale documento)\b",
        ],
        entity_extractors={
            "top_k": r"\b(?:top[_ -]?k|top|primi?)\s*(\d{1,2})\b",
            "document_id": r"\bdoc(?:ument)?[_ -]?id[:= ]([a-zA-Z0-9\-_:]+)\b",
        },
    ),
    IntentRule(
        intent="question_answering",
        suggested_engine="knowledge+inference",
        patterns=[
            r"\b(spiega|riassumi|answer|rispondi|spiegami|summarize|summary|riassunto)\b",
            r"\?$",
        ],
    ),
    IntentRule(
        intent="run_inference",
        suggested_engine="inference",
        patterns=[
            r"\b(genera|generate|completa|complete|continue|continuare|scrivi|write)\b",
            r"\b(prompt|completion|completions)\b",
        ],
        entity_extractors={
            "max_tokens": r"\bmax[_ -]?tokens?[:= ](\d{1,5})\b",
            "temperature": r"\btemperature[:= ]([0-9]+(?:\.[0-9]+)?)\b",
            "model_id": r"\bmodel[_ -]?id[:= ]([a-zA-Z0-9\-_.\/]+)\b",
        },
    ),
    IntentRule(
        intent="list_models",
        suggested_engine="inference",
        patterns=[
            r"\b(lista modelli|list models|available models|modelli disponibili)\b",
        ],
    ),
    IntentRule(
        intent="load_model",
        suggested_engine="inference",
        patterns=[
            r"\b(carica modello|load model|load the model)\b",
        ],
        entity_extractors={
            "model_id": r"\bmodel[_ -]?id[:= ]([a-zA-Z0-9\-_.\/]+)\b",
        },
    ),
    IntentRule(
        intent="ingest_document",
        suggested_engine="document",
        patterns=[
            r"\b(ingest|indicizza|index|upload|carica documento|importa documento)\b",
        ],
        entity_extractors={
            "filename": r"\bfile(?:name)?[:= ]([^\s]+)\b",
        },
    ),
    IntentRule(
        intent="delete_document",
        suggested_engine="document",
        patterns=[
            r"\b(delete document|elimina documento|rimuovi documento)\b",
        ],
        entity_extractors={
            "document_id": r"\bdoc(?:ument)?[_ -]?id[:= ]([a-zA-Z0-9\-_:]+)\b",
        },
    ),
    IntentRule(
        intent="admin_action",
        suggested_engine="administration",
        patterns=[
            r"\b(config|configurazione|settings|amministrazione|admin|utente|ruolo|permesso)\b",
        ],
    ),
]


class HeuristicIntentClassifier:
    """Weighted regex classifier with simple entity extraction."""

    def __init__(self, rules: list[IntentRule] | None = None):
        self._rules = rules or DEFAULT_INTENT_RULES

    def classify(self, text: str) -> tuple[str, float, dict, str, list[tuple[str, float, str]]]:
        norm = text.strip().lower()
        scored: list[tuple[str, float, str, dict, str]] = []

        for rule in self._rules:
            score = 0.0
            entities: dict = {}
            reasons: list[str] = []

            for pattern in rule.patterns:
                if re.search(pattern, norm, re.IGNORECASE):
                    score += 0.35
                    reasons.append(pattern)

            for entity_name, entity_pattern in rule.entity_extractors.items():
                match = re.search(entity_pattern, norm, re.IGNORECASE)
                if match:
                    raw = match.group(1)
                    entities[entity_name] = self._coerce_entity(entity_name, raw)
                    score += 0.1
                    reasons.append(f"entity:{entity_name}")

            if norm.endswith("?") and rule.intent in {"question_answering", "search_knowledge"}:
                score += 0.15
                reasons.append("question_mark")

            if score > 0:
                scored.append(
                    (
                        rule.intent,
                        min(score, 0.99),
                        ", ".join(reasons),
                        entities,
                        rule.suggested_engine,
                    )
                )

        if not scored:
            return "run_inference", 0.25, {}, "inference", [("run_inference", 0.25, "fallback")]

        scored.sort(key=lambda item: item[1], reverse=True)
        best = scored[0]
        candidates = [(intent, score, reason) for intent, score, reason, _, _ in scored[:5]]
        return best[0], best[1], best[3], best[4], candidates

    @staticmethod
    def _coerce_entity(name: str, value: str):
        if name in {"top_k", "max_tokens"}:
            return int(value)
        if name == "temperature":
            return float(value)
        return value
