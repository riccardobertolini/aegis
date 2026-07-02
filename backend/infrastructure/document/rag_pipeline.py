"""RAG pipeline — retrieve-then-generate with Mamba SSM."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from backend.domain.ports.knowledge import IKnowledgePort, SearchQuery
from backend.domain.ports.inference import IInferencePort


@dataclass
class RAGRequest:
    question: str
    top_k: int = 5
    model_id: str | None = None
    max_tokens: int = 512
    temperature: float = 0.7
    filters: dict = field(default_factory=dict)
    include_sources: bool = True


@dataclass
class RAGResponse:
    answer: str
    sources: list[dict] = field(default_factory=list)
    model_id: str | None = None
    retrieved_chunks: int = 0


class RAGPipeline:
    """
    Retrieve → Augment → Generate.

    1. Embed the question and retrieve top-k chunks from ChromaDB.
    2. Build a context-augmented prompt.
    3. Forward through the Mamba SSM inference engine.
    """

    PROMPT_TEMPLATE = (
        "Use the following context to answer the question.\n"
        "If the answer is not in the context, say so honestly.\n\n"
        "Context:\n{context}\n\n"
        "Question: {question}\n"
        "Answer:"
    )

    def __init__(
        self,
        knowledge: IKnowledgePort,
        inference: IInferencePort,
        default_model_id: str | None = None,
    ):
        self._knowledge = knowledge
        self._inference = inference
        self._default_model = default_model_id

    async def run(self, req: RAGRequest) -> RAGResponse:
        # 1. Retrieve
        results = await self._knowledge.search(
            SearchQuery(text=req.question, top_k=req.top_k, filters=req.filters)
        )

        # 2. Build context
        context_parts = []
        sources = []
        for i, r in enumerate(results, 1):
            context_parts.append(f"[{i}] {r.document.content}")
            if req.include_sources:
                sources.append({
                    "index": i,
                    "doc_id": r.document.id,
                    "score": round(r.score, 4),
                    "metadata": r.document.metadata,
                    "excerpt": r.document.content[:200],
                })

        context = "\n\n".join(context_parts) if context_parts else "No relevant context found."
        prompt = self.PROMPT_TEMPLATE.format(context=context, question=req.question)

        # 3. Generate via Mamba SSM
        model_id = req.model_id or self._default_model
        response = await self._inference.generate(
            prompt=prompt,
            model_id=model_id,
            max_tokens=req.max_tokens,
            temperature=req.temperature,
        )

        return RAGResponse(
            answer=response.text,
            sources=sources,
            model_id=model_id,
            retrieved_chunks=len(results),
        )

    async def stream(self, req: RAGRequest):
        """Async generator — yields text tokens as they are produced."""
        results = await self._knowledge.search(
            SearchQuery(text=req.question, top_k=req.top_k, filters=req.filters)
        )
        context_parts = [f"[{i+1}] {r.document.content}" for i, r in enumerate(results)]
        context = "\n\n".join(context_parts) if context_parts else "No relevant context found."
        prompt = self.PROMPT_TEMPLATE.format(context=context, question=req.question)

        model_id = req.model_id or self._default_model
        async for token in self._inference.stream(
            prompt=prompt,
            model_id=model_id,
            max_tokens=req.max_tokens,
            temperature=req.temperature,
        ):
            yield token
