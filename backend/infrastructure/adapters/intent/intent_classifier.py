"""Offline intent classifier using TF-IDF + cosine similarity.

No external model, no network call, no GPU required.
Training corpus is the keyword seed catalogue below; it can be
extended via add_examples() without restarting the service.
"""
from __future__ import annotations

import math
import re
from collections import defaultdict
from typing import Sequence

from backend.shared.logging import get_logger

from .models import IntentLabel, IntentPrediction

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Seed training corpus  (intent → list of representative phrases)
# ---------------------------------------------------------------------------
_SEED_CORPUS: dict[IntentLabel, list[str]] = {
    IntentLabel.CLASSIFICATION: [
        "classify this text", "what category is this", "label this document",
        "categorize the following", "assign a class to", "topic classification",
        "is this spam", "sentiment classification", "classify the email",
    ],
    IntentLabel.DOCUMENT_ANALYSIS: [
        "analyze this document", "summarize the pdf", "what does this file say",
        "review the report", "analyse the contract", "document analysis",
        "extract information from the document", "read this file",
    ],
    IntentLabel.EXTRACTION: [
        "extract data from", "pull out the fields", "get the values from",
        "extract structured data", "parse the table", "retrieve the numbers",
        "extract dates and names", "data extraction",
    ],
    IntentLabel.NER: [
        "find named entities", "identify persons and places", "NER",
        "named entity recognition", "who is mentioned", "locate organisations",
        "extract people companies locations", "entity extraction",
    ],
    IntentLabel.SUMMARY: [
        "summarize this", "give me a summary", "tl;dr", "brief overview",
        "condense the following", "short version of", "key points from",
        "abstract of the paper", "summarise in three sentences",
    ],
    IntentLabel.TRANSLATION: [
        "translate to italian", "translate this text", "traduce al español",
        "übersetz auf deutsch", "traduci in italiano", "translate into french",
        "language translation", "convert to english",
    ],
    IntentLabel.REWRITE: [
        "rewrite this paragraph", "rephrase the sentence", "improve the text",
        "make it more formal", "simplify the language", "paraphrase this",
        "fix the grammar", "reword the following",
    ],
    IntentLabel.QA: [
        "answer my question", "what is the capital of", "who invented",
        "when did", "how does", "why is", "question answering",
        "tell me about", "explain the concept of",
    ],
    IntentLabel.RAG: [
        "search the knowledge base", "find in my documents", "look up in kb",
        "retrieval augmented generation", "search my files", "query the index",
        "find relevant passages", "rag query", "semantic search over documents",
    ],
    IntentLabel.CONVERSATION: [
        "hello", "hi there", "how are you", "good morning", "chat with me",
        "let's talk", "I need help", "can you assist", "what can you do",
        "continue our conversation",
    ],
    IntentLabel.TIMESERIES: [
        "analyze the time series", "forecast the trend", "anomaly detection",
        "predict future values", "time series analysis", "detect spikes",
        "plot the metrics over time", "seasonal decomposition",
    ],
    IntentLabel.LOG_ANALYSIS: [
        "analyze the logs", "parse log file", "find errors in logs",
        "log analysis", "search for exceptions", "what went wrong",
        "stacktrace analysis", "error pattern in logs",
    ],
    IntentLabel.SPEECH: [
        "transcribe audio", "speech to text", "convert voice to text",
        "transcription", "audio transcription", "recognize speech",
        "process the audio file", "stt",
    ],
}


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


class TfIdfClassifier:
    """Minimal TF-IDF vectoriser + cosine similarity, pure Python."""

    def __init__(self) -> None:
        self._corpus: list[tuple[IntentLabel, list[str]]] = []  # (label, tokens)
        self._idf: dict[str, float] = {}
        self._fitted = False

    def fit(self, corpus: dict[IntentLabel, list[str]]) -> None:
        self._corpus = []
        for label, phrases in corpus.items():
            for phrase in phrases:
                self._corpus.append((label, _tokenize(phrase)))
        self._compute_idf()
        self._fitted = True

    def _compute_idf(self) -> None:
        n = len(self._corpus)
        df: dict[str, int] = defaultdict(int)
        for _, tokens in self._corpus:
            for t in set(tokens):
                df[t] += 1
        self._idf = {t: math.log((n + 1) / (count + 1)) + 1 for t, count in df.items()}

    def _tfidf_vector(self, tokens: list[str]) -> dict[str, float]:
        tf: dict[str, float] = defaultdict(float)
        for t in tokens:
            tf[t] += 1.0
        n = len(tokens) or 1
        return {t: (freq / n) * self._idf.get(t, 1.0) for t, freq in tf.items()}

    @staticmethod
    def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
        dot = sum(a.get(t, 0.0) * v for t, v in b.items())
        norm_a = math.sqrt(sum(v * v for v in a.values())) or 1e-9
        norm_b = math.sqrt(sum(v * v for v in b.values())) or 1e-9
        return dot / (norm_a * norm_b)

    def predict(self, text: str, top_n: int = 3) -> list[tuple[IntentLabel, float]]:
        if not self._fitted:
            raise RuntimeError("Classifier not fitted.")
        q_vec = self._tfidf_vector(_tokenize(text))
        scores: dict[IntentLabel, float] = defaultdict(float)
        counts: dict[IntentLabel, int]   = defaultdict(int)
        for label, tokens in self._corpus:
            doc_vec = self._tfidf_vector(tokens)
            scores[label] += self._cosine(q_vec, doc_vec)
            counts[label] += 1
        avg = {label: scores[label] / counts[label] for label in scores}
        return sorted(avg.items(), key=lambda x: x[1], reverse=True)[:top_n]


class IntentClassifier:
    """
    High-level intent classifier.

    Uses TF-IDF cosine similarity over a seed corpus.
    Fully offline — no network, no GPU, no external model files.
    Can be extended at runtime via add_examples().
    """

    def __init__(
        self,
        confidence_threshold: float = 0.05,
        ambiguity_margin: float = 0.02,
    ) -> None:
        self._threshold  = confidence_threshold
        self._margin     = ambiguity_margin
        self._clf        = TfIdfClassifier()
        self._corpus     = {k: list(v) for k, v in _SEED_CORPUS.items()}
        self._clf.fit(self._corpus)

    def add_examples(self, intent: IntentLabel, phrases: list[str]) -> None:
        """Extend the corpus without restart (re-fits in place)."""
        self._corpus.setdefault(intent, []).extend(phrases)
        self._clf.fit(self._corpus)

    def classify(self, text: str) -> IntentPrediction:
        """Classify *text* and return an IntentPrediction."""
        candidates = self._clf.predict(text, top_n=3)
        if not candidates:
            return IntentPrediction(
                intent=IntentLabel.UNKNOWN,
                confidence=0.0,
                fallback=True,
            )
        best_label, best_score = candidates[0]
        top_candidates = [(str(lbl), round(sc, 4)) for lbl, sc in candidates]

        if best_score < self._threshold:
            logger.info("intent.classify.fallback", score=best_score, text=text[:80])
            return IntentPrediction(
                intent=IntentLabel.UNKNOWN,
                confidence=best_score,
                top_candidates=top_candidates,
                fallback=True,
            )

        ambiguous = (
            len(candidates) >= 2
            and (best_score - candidates[1][1]) < self._margin
        )
        logger.info(
            "intent.classify.done",
            intent=best_label,
            confidence=round(best_score, 4),
            ambiguous=ambiguous,
        )
        return IntentPrediction(
            intent=best_label,
            confidence=best_score,
            top_candidates=top_candidates,
            ambiguous=ambiguous,
            fallback=False,
        )
