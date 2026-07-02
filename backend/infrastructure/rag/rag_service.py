"""RAGService — Retrieval-Augmented Generation orchestrator.

Pipeline:
    query → LocalEmbedder → ChromaDB search → context assembly
         → InferencePort (CoreAI) → RAGResponse with cited sources
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from backend.domain.ports.knowledge import IKnowledgePort, SearchQuery, SearchResult
from backend.domain.ports.inference import IInferencePort, InferenceRequest

logger = logging.getLogger(__name__)


@dataclass
class RAGRequest:
    query: str
    session_id: str = ""
    model_id: str = ""
    top_k: int = 5
    max_tokens: int = 512
    temperature: float = 0.3
    filters: dict = field(default_factory=dict)
    knowledge_base_id: str = ""  # empty = search all
    include_sources: bool = True


@dataclass
class RAGSource:
    document_id: str
    chunk_text: str
    score: float
    metadata: dict = field(default_factory=dict)


@dataclass
class RAGResponse:
    answer: str
    sources: list[RAGSource] = field(default_factory=list)
    model_id: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0


class RAGService:
    """Retrieval-Augmented Generation service.

    Injects retrieved document context into the inference prompt,
    producing grounded answers with cited sources.
    All operations are local — no cloud, no API calls.
    """

    # Template for RAG prompt assembly
    _CONTEXT_TEMPLATE = (
        "You are Aegis, a helpful AI assistant. "
        "Answer the user's question using ONLY the provided context. "
        "If the context does not contain the answer, say so clearly.\n\n"
        "=== CONTEXT ===\n{context}\n=== END CONTEXT ===\n\n"
        "Question: {query}\n\nAnswer:"
    )

    def __init__(
        self,
        knowledge: IKnowledgePort,
        inference: IInferencePort,
        default_model_id: str = "",
        min_score_threshold: float = 0.0,
        max_context_chars: int = 4096,
    ) -> None:
        self._knowledge = knowledge
        self._inference = inference
        self._default_model_id = default_model_id
        self._min_score = min_score_threshold
        self._max_ctx_chars = max_context_chars

    async def query(self, request: RAGRequest) -> RAGResponse:
        """Full RAG pipeline: retrieve → augment → generate."""

        # 1. Build search query with optional KB filter
        filters = dict(request.filters)
        if request.knowledge_base_id:
            filters["knowledge_base_id"] = request.knowledge_base_id

        search_q = SearchQuery(
            text=request.query,
            top_k=request.top_k,
            filters=filters,
        )

        # 2. Retrieve relevant chunks
        try:
            results: list[SearchResult] = await self._knowledge.search(search_q)
        except Exception as exc:
            logger.warning("Knowledge search failed: %s — answering without context", exc)
            results = []

        # 3. Filter by score threshold
        filtered = [
            r for r in results if r.score >= self._min_score
        ]

        # 4. Assemble context string (truncated to max_context_chars)
        context_parts: list[str] = []
        total_chars = 0
        sources: list[RAGSource] = []

        for i, res in enumerate(filtered):
            chunk_text = res.document.content
            if total_chars + len(chunk_text) > self._max_ctx_chars:
                remaining = self._max_ctx_chars - total_chars
                if remaining > 64:
                    chunk_text = chunk_text[:remaining] + "..."
                    context_parts.append(f"[{i+1}] {chunk_text}")
                break
            context_parts.append(f"[{i+1}] {chunk_text}")
            total_chars += len(chunk_text)
            sources.append(
                RAGSource(
                    document_id=res.document.id,
                    chunk_text=res.document.content,
                    score=res.score,
                    metadata=res.document.metadata,
                )
            )

        context = "\n\n".join(context_parts) if context_parts else "No relevant documents found."

        # 5. Build augmented prompt
        prompt = self._CONTEXT_TEMPLATE.format(
            context=context,
            query=request.query,
        )

        # 6. Run inference
        model_id = request.model_id or self._default_model_id
        inf_req = InferenceRequest(
            prompt=prompt,
            model_id=model_id,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            stream=False,
            extra={},
        )
        try:
            inf_resp = await self._inference.run(inf_req)
            answer = inf_resp.text
            prompt_tokens = inf_resp.prompt_tokens
            completion_tokens = inf_resp.completion_tokens
            used_model = inf_resp.model_id
        except Exception as exc:
            logger.error("RAG inference failed: %s", exc)
            answer = f"[Inference error: {exc}]"
            prompt_tokens = 0
            completion_tokens = 0
            used_model = model_id

        return RAGResponse(
            answer=answer,
            sources=sources if request.include_sources else [],
            model_id=used_model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )

    async def ingest_and_query(
        self, documents, query: str, **kwargs
    ) -> RAGResponse:
        """Convenience: ingest documents then immediately query."""
        from backend.domain.ports.knowledge import Document
        docs = [
            Document(id=d["id"], content=d["content"], metadata=d.get("metadata", {}))
            for d in documents
        ]
        await self._knowledge.ingest(docs)
        return await self.query(RAGRequest(query=query, **kwargs))
