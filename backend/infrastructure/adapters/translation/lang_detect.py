"""Offline language detection.

Primary: ``langdetect`` library (pure Python, offline).
Fallback: n-gram profile matching against small built-in profiles.
"""
from __future__ import annotations

import re

_TRIGRAMS: dict[str, list[str]] = {
    "it": ["che", "del", "per", "con", "una", "non", "dei", "gli", "nel", "dal"],
    "en": ["the", "and", "for", "with", "this", "that", "are", "was", "not", "have"],
    "de": ["die", "der", "und", "ein", "nicht", "ist", "das", "mit", "ich", "auch"],
    "fr": ["les", "des", "est", "une", "pour", "pas", "que", "dans", "qui", "avec"],
}

_SUPPORTED = {"it", "en", "de", "fr"}


def detect_language(text: str) -> tuple[str, float]:
    """Return (iso_code, confidence). Confidence in [0, 1]."""
    if not text.strip():
        return "en", 0.0

    # Try langdetect first
    try:
        from langdetect import detect_langs  # type: ignore

        results = detect_langs(text)
        for r in results:
            lang = r.lang.split("-")[0].lower()  # "zh-cn" → "zh"
            if lang in _SUPPORTED:
                return lang, float(r.prob)
        # not in supported — return best anyway
        top = results[0]
        return top.lang.split("-")[0].lower(), float(top.prob)
    except Exception:
        pass

    # Fallback: simple word-overlap scoring
    tokens = set(re.findall(r"\b\w+\b", text.lower()))
    scores: dict[str, int] = {}
    for lang, grams in _TRIGRAMS.items():
        scores[lang] = sum(1 for g in grams if g in tokens)

    best = max(scores, key=lambda k: scores[k])
    total = sum(scores.values()) or 1
    return best, scores[best] / total
