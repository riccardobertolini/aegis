"""KnowledgeEngine: orchestrates embedding, indexing and RAG retrieval.

Implements IKnowledgePort.
"""
from __future__ import annotations

import uuid
from pathlib import Path

from backend.domain.ports.knowledge import IKnowledgePort
from backend.shared.logging import get_logger

from ..document.document_engine import DocumentEngine
from ..document.models import TextChunk
from .embedding_engine import EmbeddingEngine
from .models import KnowledgeBase, RagContext, RetrievedChunk
from .vector_store import ChromaVectorStore

logger = get_logger(__name__)


class KnowledgeEngine(IKnowledgePort):
    """
    Single façade for:
    - Managing multiple knowledge bases
    - Ingesting documents (parse → chunk → embed → index)
    - RAG retrieval (embed query → vector search → rank → build context)
    - Incremental re-indexing and index integrity
    """

    def __init__(
        self,
        document_engine: DocumentEngine | None = None,
        embedding_engine: EmbeddingEngine | None = None,
        vector_store: ChromaVectorStore | None = None,
        chunk_size: int = 512,
        overlap: int = 64,
        top_k: int = 5,
        max_context_chars: int = 4096,
    ) -> None:
        self._doc_engine = document_engine or DocumentEngine(chunk_size=chunk_size, overlap=overlap)
        self._embedding = embedding_engine or EmbeddingEngine()
        self._store = vector_store or ChromaVectorStore()
        self._top_k = top_k
        self._max_context_chars = max_context_chars
        # In-memory registry of KBs (persisted to Chroma metadata in production)
        self._kb_registry: dict[str, KnowledgeBase] = {}

    # ------------------------------------------------------------------ #
    # Knowledge Base management                                            #
    # ------------------------------------------------------------------ #

    def create_kb(
        self,
        name: str,
        description: str = "",
        category: str = "general",
        assistant_id: str | None = None,
    ) -> KnowledgeBase:
        """Create and register a new knowledge base."""
        kb = KnowledgeBase(
            kb_id=str(uuid.uuid4()),
            name=name,
            description=description,
            category=category,
            assistant_id=assistant_id,
        )
        self._kb_registry[kb.kb_id] = kb
        logger.info("kb.created", kb_id=kb.kb_id, name=name)
        return kb

    def get_kb(self, kb_id: str) -> KnowledgeBase:
        kb = self._kb_registry.get(kb_id)
        if kb is None:
            raise KeyError(f"KnowledgeBase not found: {kb_id}")
        return kb

    def list_kbs(
        self,
        category: str | None = None,
        assistant_id: str | None = None,
    ) -> list[KnowledgeBase]:
        kbs = list(self._kb_registry.values())
        if category:
            kbs = [kb for kb in kbs if kb.category == category]
        if assistant_id:
            kbs = [kb for kb in kbs if kb.assistant_id == assistant_id]
        return kbs

    def delete_kb(self, kb_id: str) -> None:
        self._kb_registry.pop(kb_id, None)
        self._store.delete_collection(kb_id)
        logger.info("kb.deleted", kb_id=kb_id)

    # ------------------------------------------------------------------ #
    # Ingestion                                                            #
    # ------------------------------------------------------------------ #

    def add_document(
        self,
        kb_id: str,
        path: str | Path,
        force_reindex: bool = False,
    ) -> int:
        """Parse, chunk, embed and index a document into *kb_id*.

        Returns:
            Number of chunks indexed.
        """
        kb = self.get_kb(kb_id)
        p = Path(path)
        doc, chunks = self._doc_engine.ingest(p)

        if force_reindex:
            self._store.delete_by_document(kb_id, chunks[0].document_id if chunks else "")

        self._index_chunks(kb_id, chunks)
        kb.document_count += 1
        kb.chunk_count += len(chunks)
        logger.info("kb.document.added", kb_id=kb_id, path=str(p), chunks=len(chunks))
        return len(chunks)

    def remove_document(self, kb_id: str, document_id: str) -> None:
        """Remove all chunks for *document_id* from *kb_id*."""
        kb = self.get_kb(kb_id)
        self._store.delete_by_document(kb_id, document_id)
        kb.document_count = max(0, kb.document_count - 1)
        logger.info("kb.document.removed", kb_id=kb_id, document_id=document_id)

    def reindex(self, kb_id: str, path: str | Path) -> int:
        """Force re-parse and re-embed an existing document."""
        return self.add_document(kb_id, path, force_reindex=True)

    def _index_chunks(self, kb_id: str, chunks: list[TextChunk]) -> None:
        if not chunks:
            return
        texts = [c.text for c in chunks]
        embeddings = self._embedding.embed(texts)
        metadatas = [
            {
                "document_id": c.document_id,
                "source_path": c.source_path,
                "chunk_index": c.chunk_index,
                **{k: str(v) for k, v in c.metadata.items()},
            }
            for c in chunks
        ]
        self._store.upsert(
            kb_id=kb_id,
            chunk_ids=[c.chunk_id for c in chunks],
            embeddings=embeddings,
            texts=texts,
            metadatas=metadatas,
        )

    # ------------------------------------------------------------------ #
    # Retrieval & RAG                                                      #
    # ------------------------------------------------------------------ #

    def retrieve(
        self,
        kb_id: str,
        query: str,
        top_k: int | None = None,
        filter_metadata: dict | None = None,
    ) -> list[RetrievedChunk]:
        """Vector-similarity search in *kb_id* for *query*."""
        k = top_k or self._top_k
        q_emb = self._embedding.embed_one(query)
        return self._store.query(kb_id, q_emb, top_k=k, filter_metadata=filter_metadata)

    def retrieve_multi(
        self,
        kb_ids: list[str],
        query: str,
        top_k: int | None = None,
    ) -> list[RetrievedChunk]:
        """Retrieve across multiple knowledge bases, then re-rank by score."""
        k = top_k or self._top_k
        all_chunks: list[RetrievedChunk] = []
        for kb_id in kb_ids:
            all_chunks.extend(self.retrieve(kb_id, query, top_k=k))
        return sorted(all_chunks, key=lambda c: c.score, reverse=True)[:k]

    def build_rag_context(
        self,
        query: str,
        kb_ids: list[str],
        top_k: int | None = None,
        max_chars: int | None = None,
    ) -> RagContext:
        """Full RAG pipeline: retrieve + rank + build context for inference."""
        chunks = self.retrieve_multi(kb_ids, query, top_k=top_k)
        return RagContext.build(
            query=query,
            chunks=chunks,
            max_chars=max_chars or self._max_context_chars,
        )

    # ------------------------------------------------------------------ #
    # Index integrity                                                      #
    # ------------------------------------------------------------------ #

    def integrity_check(self, kb_id: str) -> dict:
        """Return basic stats for index integrity verification."""
        count = self._store.count(kb_id)
        kb = self.get_kb(kb_id)
        ok = count >= 0
        return {
            "kb_id": kb_id,
            "name": kb.name,
            "indexed_chunks": count,
            "registered_chunks": kb.chunk_count,
            "consistent": count == kb.chunk_count,
            "status": "ok" if ok else "error",
        }
