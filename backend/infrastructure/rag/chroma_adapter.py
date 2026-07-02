"""ChromaKnowledgeAdapter — implements IKnowledgePort via ChromaDB embedded.

ChromaDB runs entirely in-process (no server, no port, no network).
Data persists in a local directory configured via `chroma_persist_dir`.
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Optional

from backend.domain.ports.knowledge import (
    Document,
    IKnowledgePort,
    SearchQuery,
    SearchResult,
)
from backend.infrastructure.rag.embedder import LocalEmbedder
from backend.infrastructure.rag.chunker import TextChunker, Chunk

logger = logging.getLogger(__name__)


class ChromaKnowledgeAdapter(IKnowledgePort):
    """Vector store backed by ChromaDB embedded + LocalEmbedder.

    One ChromaDB collection per knowledge-base name.
    Documents are stored as chunks; each chunk is one ChromaDB entry.
    The document_id is stored in chunk metadata so we can delete all
    chunks of a document atomically.
    """

    def __init__(
        self,
        persist_dir: str,
        embedder: LocalEmbedder,
        chunker: TextChunker,
        collection_name: str = "aegis_default",
    ) -> None:
        self._persist_dir = persist_dir
        self._embedder = embedder
        self._chunker = chunker
        self._collection_name = collection_name
        self._client = None
        self._collection = None
        self._executor = None

    # ------------------------------------------------------------------
    # IKnowledgePort
    # ------------------------------------------------------------------

    async def ingest(self, documents: list[Document]) -> None:
        """Chunk, embed, and store documents."""
        if not documents:
            return

        all_chunks: list[Chunk] = []
        for doc in documents:
            chunks = self._chunker.chunk_text(
                document_id=doc.id,
                text=doc.content,
                base_metadata=doc.metadata,
            )
            all_chunks.extend(chunks)

        if not all_chunks:
            logger.warning("ingest: no chunks produced from %d documents", len(documents))
            return

        texts = [c.text for c in all_chunks]
        embeddings = await self._embedder.embed_texts(texts)

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self._executor,
            self._upsert_sync,
            all_chunks,
            embeddings,
        )
        logger.info(
            "Ingested %d doc(s) → %d chunk(s) into collection '%s'",
            len(documents),
            len(all_chunks),
            self._collection_name,
        )

    async def search(self, query: SearchQuery) -> list[SearchResult]:
        """Embed query and retrieve top-k results from ChromaDB."""
        query_embedding = await self._embedder.embed_query(query.text)

        loop = asyncio.get_event_loop()
        raw = await loop.run_in_executor(
            self._executor,
            self._query_sync,
            query_embedding,
            query.top_k,
            query.filters,
        )
        return raw

    async def delete(self, document_id: str) -> None:
        """Delete all chunks belonging to a document."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self._executor,
            self._delete_by_document_id_sync,
            document_id,
        )
        logger.info("Deleted chunks for document '%s'", document_id)

    async def list_documents(
        self, page: int = 0, page_size: int = 20
    ) -> list[Document]:
        """Return unique documents (de-duplicated by document_id)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            self._list_documents_sync,
            page,
            page_size,
        )

    # ------------------------------------------------------------------
    # Sync helpers (run in thread pool)
    # ------------------------------------------------------------------

    def _get_collection(self):
        if self._collection is None:
            import chromadb  # type: ignore
            from chromadb.config import Settings  # type: ignore

            self._client = chromadb.PersistentClient(
                path=self._persist_dir,
                settings=Settings(
                    anonymized_telemetry=False,  # no telemetry ever
                    allow_reset=True,
                ),
            )
            self._collection = self._client.get_or_create_collection(
                name=self._collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    def _upsert_sync(
        self,
        chunks: list[Chunk],
        embeddings: list[list[float]],
    ) -> None:
        coll = self._get_collection()
        ids = [f"{c.document_id}__chunk_{c.chunk_index}" for c in chunks]
        metadatas = [
            {"document_id": c.document_id, **c.metadata} for c in chunks
        ]
        coll.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=[c.text for c in chunks],
            metadatas=metadatas,
        )

    def _query_sync(
        self,
        query_embedding: list[float],
        top_k: int,
        filters: dict,
    ) -> list[SearchResult]:
        coll = self._get_collection()
        where = self._build_where(filters)
        kwargs = dict(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        if where:
            kwargs["where"] = where

        try:
            result = coll.query(**kwargs)
        except Exception as exc:
            logger.warning("ChromaDB query error: %s", exc)
            return []

        results: list[SearchResult] = []
        docs_list = result.get("documents", [[]])[0]
        metas_list = result.get("metadatas", [[]])[0]
        dists_list = result.get("distances", [[]])[0]

        for doc_text, meta, dist in zip(docs_list, metas_list, dists_list):
            # Cosine distance → similarity score (0=identical, 2=opposite)
            score = max(0.0, 1.0 - dist)
            results.append(
                SearchResult(
                    document=Document(
                        id=meta.get("document_id", ""),
                        content=doc_text,
                        metadata=meta,
                    ),
                    score=score,
                )
            )
        return results

    def _delete_by_document_id_sync(self, document_id: str) -> None:
        coll = self._get_collection()
        try:
            coll.delete(where={"document_id": {"$eq": document_id}})
        except Exception as exc:
            logger.warning("ChromaDB delete error for '%s': %s", document_id, exc)

    def _list_documents_sync(self, page: int, page_size: int) -> list[Document]:
        coll = self._get_collection()
        try:
            result = coll.get(include=["documents", "metadatas"])
        except Exception:
            return []

        # De-duplicate by document_id
        seen: dict[str, Document] = {}
        docs_list = result.get("documents") or []
        metas_list = result.get("metadatas") or []
        for doc_text, meta in zip(docs_list, metas_list):
            doc_id = meta.get("document_id", "")
            if doc_id and doc_id not in seen:
                seen[doc_id] = Document(
                    id=doc_id,
                    content=doc_text,
                    metadata=meta,
                )

        # Paginate
        all_docs = list(seen.values())
        start = page * page_size
        return all_docs[start: start + page_size]

    @staticmethod
    def _build_where(filters: dict) -> Optional[dict]:
        """Convert simple key=value filters to ChromaDB where clause."""
        if not filters:
            return None
        if len(filters) == 1:
            k, v = next(iter(filters.items()))
            return {k: {"$eq": v}}
        return {"$and": [{k: {"$eq": v}} for k, v in filters.items()]}
