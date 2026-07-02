"""Shared contracts for Intent Engine and all modalities."""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ------------------------------------------------------------------ #
# Intent taxonomy                                                      #
# ------------------------------------------------------------------ #

class IntentLabel(str, Enum):
    CLASSIFICATION   = "classification"
    DOCUMENT_ANALYSIS = "document_analysis"
    EXTRACTION       = "extraction"
    NER              = "ner"
    SUMMARY          = "summary"
    TRANSLATION      = "translation"
    REWRITE          = "rewrite"
    QA               = "qa"
    RAG              = "rag"
    CONVERSATION     = "conversation"
    TIMESERIES       = "timeseries"
    LOG_ANALYSIS     = "log_analysis"
    SPEECH           = "speech"
    UNKNOWN          = "unknown"


# ------------------------------------------------------------------ #
# Common I/O contracts for all modalities                              #
# ------------------------------------------------------------------ #

class ModalityRequest(BaseModel):
    """Universal input contract consumed by every modality."""
    session_id: str
    intent: IntentLabel
    text: str                                    # primary user input
    documents: list[str] = Field(default_factory=list)   # optional file paths
    kb_ids: list[str]    = Field(default_factory=list)   # optional KB scope
    parameters: dict[str, Any] = Field(default_factory=dict)  # mode-specific extras
    context: dict[str, Any]    = Field(default_factory=dict)  # conversation history


class ModalityResponse(BaseModel):
    """Universal output contract returned by every modality."""
    session_id: str
    intent: IntentLabel
    result: Any                        # mode-specific payload
    confidence: float = 1.0
    citations: list[dict[str, str]] = Field(default_factory=list)
    metadata: dict[str, Any]        = Field(default_factory=dict)
    fallback_used: bool = False
    error: str | None = None


# ------------------------------------------------------------------ #
# Intent classification result                                         #
# ------------------------------------------------------------------ #

class IntentPrediction(BaseModel):
    intent: IntentLabel
    confidence: float
    top_candidates: list[tuple[str, float]] = Field(default_factory=list)
    ambiguous: bool = False
    fallback: bool = False
