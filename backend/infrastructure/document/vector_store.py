"""ChromaDB embedded vector store — fully local, no server required."""
from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Any

from backend.domain.ports.knowledge import Document, SearchQuery, SearchResult

logger = logging.getLogger(__name__)


class ChromaVectorStore:
    """
    Thin wrapper around chromadb.Client (embedded, persistent).
    Collection name maps to a knowledge-base / corpus ID.
    """

    def __init__(self, persist_dir: Path, collection_name: str = "aegis_rag"):
        self._persist_dir = persist_dir
        self._collection_name = collection_name
        self._client = None
        self._collection = None

    def _init(self):
        if self._client is not None:
            return
        try:
            import chromadb  # type: ignore
            self._persist_dir.mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(path=str(self._persist_dir))
            self._collection = self._client.get_or_create_collection(
                name=self._collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info("ChromaDB ready at %s / %s", self._persist_dir, self._collection_name)
        except ImportError:
            raise RuntimeError(
                "chromadb is not installed. Add it to requirements/base.txt "
                "and install offline via wheelhouse."
            )

    # ── write ──────────────────────────────────────────────────────────────────

    def upsert(
        self,
        doc_id: str,
        chunks: list[str],
        embeddings: list[list[float]],
        metadata: dict | None = None,
    ) -> None:
        self._init()
        ids = [f"{doc_id}::{i}" for i in range(len(chunks))]
        metas = [{"doc_id": doc_id, **(metadata or {})} for _ in chunks]
        self._collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metas,
        )

    def delete_by_doc_id(self, doc_id: str) -> None:
        self._init()
        results = self._collection.get(where={"doc_id": doc_id})
        if results["ids"]:
            self._collection.delete(ids=results["ids"])

    # ── read ───────────────────────────────────────────────────────────────────

    def query(
        self,
        embedding: list[float],
        top_k: int = 5,
        filters: dict | None = None,
    ) -> list[dict[str, Any]]:
        self._init()
        kwargs: dict[str, Any] = {
            "query_embeddings": [embedding],
            "n_results": top_k,
            "include": ["documents", "metadatas", "distances"],
        }
        if filters:
            kwargs["where"] = filters
        results = self._collection.query(**kwargs)
        out = []
        for i, chunk_id in enumerate(results["ids"][0]):
            out.append({
                "id": chunk_id,
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
            })
        return out

    def count(self) -> int:
        self._init()
        return self._collection.count()

    def list_doc_ids(self) -> list[str]:
        self._init()
        results = self._collection.get(include=["metadatas"])
        seen: set[str] = set()
        for meta in results.get("metadatas") or []:
            if meta and "doc_id" in meta:
                seen.add(meta["doc_id"])
        return sorted(seen)
