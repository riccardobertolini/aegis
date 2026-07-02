"""Documents / RAG API client methods."""
from __future__ import annotations

from pathlib import Path

import httpx

from .base import AegisClient


class DocumentsMixin(AegisClient):
    """Methods for /api/v1/documents endpoints."""

    BASE = "/api/v1/documents"

    def upload_document(self, file_path: str | Path, chunk_size: int = 512, chunk_overlap: int = 64) -> dict:
        """POST /api/v1/documents/upload (multipart)"""
        path = Path(file_path)
        with httpx.Client(base_url=self.base_url, headers=self._headers, timeout=60.0) as c:
            with open(path, "rb") as f:
                r = c.post(
                    f"{self.BASE}/upload",
                    files={"file": (path.name, f)},
                    params={"chunk_size": chunk_size, "chunk_overlap": chunk_overlap},
                )
            r.raise_for_status()
            return r.json()

    def list_documents(self, page: int = 0, page_size: int = 20) -> list[dict]:
        """GET /api/v1/documents/"""
        return self._get(f"{self.BASE}/", page=page, page_size=page_size)

    def get_document(self, document_id: str) -> dict:
        """GET /api/v1/documents/{document_id}"""
        return self._get(f"{self.BASE}/{document_id}")

    def delete_document(self, document_id: str) -> None:
        """DELETE /api/v1/documents/{document_id}"""
        self._delete(f"{self.BASE}/{document_id}")

    def rag_query(
        self,
        question: str,
        top_k: int = 5,
        model_id: str | None = None,
        max_tokens: int = 512,
        temperature: float = 0.7,
        filters: dict | None = None,
    ) -> dict:
        """POST /api/v1/documents/rag/query"""
        return self._post(
            f"{self.BASE}/rag/query",
            json={
                "question": question,
                "top_k": top_k,
                "model_id": model_id,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "filters": filters or {},
                "stream": False,
            },
        )

    def semantic_search(self, query: str, top_k: int = 5, filters: dict | None = None) -> list[dict]:
        """POST /api/v1/documents/search"""
        return self._post(
            f"{self.BASE}/search",
            json={"query": query, "top_k": top_k, "filters": filters or {}},
        )
