"""ChromaDB embedded vector store — 100% local, no server."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.shared.logging import get_logger

from .models import RetrievedChunk

logger = get_logger(__name__)

_DEFAULT_PERSIST_DIR = Path("data/chroma")


class ChromaVectorStore:
    """
    Thin wrapper around chromadb.PersistentClient.

    Each KnowledgeBase maps to a separate Chroma collection,
    ensuring full isolation between knowledge bases.
    """

    def __init__(self, persist_dir: str | Path = _DEFAULT_PERSIST_DIR) -> None:
        self._persist_dir = Path(persist_dir)
        self._persist_dir.mkdir(parents=True, exist_ok=True)
        self._client = None  # lazy init

    def _get_client(self) -> Any:
        if self._client is None:
            try:
                import chromadb

                self._client = chromadb.PersistentClient(path=str(self._persist_dir))
                logger.info("chroma.client.init", path=str(self._persist_dir))
            except ImportError as exc:
                raise RuntimeError(
                    "chromadb is not installed. Add to requirements/base.txt."
                ) from exc
        return self._client

    def _collection(self, kb_id: str) -> Any:
        return self._get_client().get_or_create_collection(
            name=f"kb_{kb_id}",
            metadata={"hnsw:space": "cosine"},
        )

    # ------------------------------------------------------------------ #
    # Write                                                                #
    # ------------------------------------------------------------------ #

    def upsert(
        self,
        kb_id: str,
        chunk_ids: list[str],
        embeddings: list[list[float]],
        texts: list[str],
        metadatas: list[dict[str, Any]],
    ) -> None:
        """Upsert chunks into the collection for *kb_id*."""
        col = self._collection(kb_id)
        col.upsert(
            ids=chunk_ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )
        logger.info("chroma.upsert", kb_id=kb_id, count=len(chunk_ids))

    def delete_by_document(
        self,
        kb_id: str,
        document_id: str,
    ) -> None:
        """Remove all chunks belonging to *document_id* from *kb_id*."""
        col = self._collection(kb_id)
        results = col.get(where={"document_id": document_id})
        ids = results.get("ids", [])
        if ids:
            col.delete(ids=ids)
            logger.info("chroma.delete", kb_id=kb_id, document_id=document_id, removed=len(ids))

    def delete_collection(self, kb_id: str) -> None:
        """Drop entire collection for *kb_id* (used when a KB is deleted)."""
        self._get_client().delete_collection(name=f"kb_{kb_id}")
        logger.info("chroma.collection.deleted", kb_id=kb_id)

    # ------------------------------------------------------------------ #
    # Read / Retrieval                                                     #
    # ------------------------------------------------------------------ #

    def query(
        self,
        kb_id: str,
        query_embedding: list[float],
        top_k: int = 5,
        filter_metadata: dict[str, Any] | None = None,
    ) -> list[RetrievedChunk]:
        """Similarity search in *kb_id*, returns top-k chunks."""
        col = self._collection(kb_id)
        kwargs: dict[str, Any] = {"query_embeddings": [query_embedding], "n_results": top_k}
        if filter_metadata:
            kwargs["where"] = filter_metadata
        results = col.query(**kwargs)
        chunks: list[RetrievedChunk] = []
        for i, chunk_id in enumerate(results["ids"][0]):
            distance = results["distances"][0][i]
            score = 1.0 - distance  # cosine distance → similarity
            meta = results["metadatas"][0][i] or {}
            text = results["documents"][0][i] or ""
            chunks.append(
                RetrievedChunk(
                    chunk_id=chunk_id,
                    document_id=meta.get("document_id", ""),
                    source_path=meta.get("source_path", ""),
                    text=text,
                    score=score,
                    kb_id=kb_id,
                    metadata=meta,
                )
            )
        return sorted(chunks, key=lambda c: c.score, reverse=True)

    def count(self, kb_id: str) -> int:
        """Return total chunk count in *kb_id*."""
        return self._collection(kb_id).count()

    def list_collection_names(self) -> list[str]:
        """Return all collection names."""
        return [c.name for c in self._get_client().list_collections()]
