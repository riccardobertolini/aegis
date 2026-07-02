"""KnowledgeService — implements IKnowledgePort (RAG search)."""
from __future__ import annotations

import asyncio
from functools import partial

from backend.domain.ports.knowledge import (
    Document,
    IKnowledgePort,
    SearchQuery,
    SearchResult,
)
from backend.infrastructure.document.embedder import IEmbedder
from backend.infrastructure.document.vector_store import ChromaVectorStore


class KnowledgeService(IKnowledgePort):
    """Wraps ChromaDB + embedder to implement semantic search."""

    def __init__(self, vector_store: ChromaVectorStore, embedder: IEmbedder):
        self._vs = vector_store
        self._embedder = embedder

    async def ingest(self, documents: list[Document]) -> None:
        loop = asyncio.get_event_loop()
        texts = [d.content for d in documents]
        embeddings = await loop.run_in_executor(None, self._embedder.embed, texts)
        for doc, emb in zip(documents, embeddings):
            self._vs.upsert(doc.id, [doc.content], [emb], doc.metadata)

    async def search(self, query: SearchQuery) -> list[SearchResult]:
        loop = asyncio.get_event_loop()
        emb = await loop.run_in_executor(
            None, self._embedder.embed, [query.text]
        )
        raw = self._vs.query(
            embedding=emb[0],
            top_k=query.top_k,
            filters=query.filters or None,
        )
        results: list[SearchResult] = []
        for item in raw:
            doc = Document(
                id=item["metadata"].get("doc_id", item["id"]),
                content=item["text"],
                metadata=item["metadata"],
            )
            # ChromaDB returns cosine distance [0,2]; convert to similarity
            score = max(0.0, 1.0 - item["distance"])
            results.append(SearchResult(document=doc, score=score))
        return results

    async def delete(self, document_id: str) -> None:
        self._vs.delete_by_doc_id(document_id)

    async def list_documents(
        self, page: int = 0, page_size: int = 20
    ) -> list[Document]:
        all_ids = self._vs.list_doc_ids()
        page_ids = all_ids[page * page_size : (page + 1) * page_size]
        docs = []
        for doc_id in page_ids:
            docs.append(Document(id=doc_id, content="", metadata={"doc_id": doc_id}))
        return docs
