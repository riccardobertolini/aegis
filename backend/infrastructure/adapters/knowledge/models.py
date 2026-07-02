"""Domain models for the Knowledge Engine."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class KnowledgeBase(BaseModel):
    """Represents a named, isolated knowledge base."""

    kb_id: str
    name: str
    description: str = ""
    category: str = "general"
    assistant_id: str | None = None  # optional: scoped to a specific assistant
    created_at: datetime = Field(default_factory=datetime.utcnow)
    document_count: int = 0
    chunk_count: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievedChunk(BaseModel):
    """A chunk returned by vector similarity search."""

    chunk_id: str
    document_id: str
    source_path: str
    text: str
    score: float  # cosine similarity, higher = more relevant
    kb_id: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class RagContext(BaseModel):
    """Context block ready to be injected into an LLM prompt."""

    query: str
    chunks: list[RetrievedChunk]
    context_text: str  # pre-formatted string for prompt injection
    citations: list[dict[str, str]]  # [{"source": path, "excerpt": ...}]
    total_tokens_estimate: int = 0

    @classmethod
    def build(
        cls,
        query: str,
        chunks: list[RetrievedChunk],
        max_chars: int = 4096,
    ) -> "RagContext":
        """Assemble context text and citations from retrieved chunks."""
        parts: list[str] = []
        citations: list[dict[str, str]] = []
        char_count = 0
        for chunk in chunks:
            if char_count + len(chunk.text) > max_chars:
                break
            parts.append(f"[{chunk.source_path}]\n{chunk.text}")
            citations.append({"source": chunk.source_path, "excerpt": chunk.text[:120]})
            char_count += len(chunk.text)
        context_text = "\n\n---\n\n".join(parts)
        return cls(
            query=query,
            chunks=chunks,
            context_text=context_text,
            citations=citations,
            total_tokens_estimate=char_count // 4,
        )
