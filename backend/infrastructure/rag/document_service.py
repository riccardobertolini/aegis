"""DocumentService — implements IDocumentPort.

Full ingest pipeline:
    file/bytes → DocumentParser → TextChunker → LocalEmbedder
                → ChromaDB (vectors) + SQLite (metadata via DocumentRepository)
"""
from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Optional

from backend.domain.ports.document import IDocumentPort, ParsedDocument
from backend.infrastructure.rag.parser import DocumentParser
from backend.infrastructure.rag.chroma_adapter import ChromaKnowledgeAdapter
from backend.domain.ports.knowledge import Document as KnowledgeDocument

logger = logging.getLogger(__name__)


class DocumentService(IDocumentPort):
    """Orchestrates document ingestion and manages metadata persistence."""

    def __init__(
        self,
        parser: DocumentParser,
        knowledge: ChromaKnowledgeAdapter,
        document_repo=None,  # Optional[SQLiteDocumentRepository]
    ) -> None:
        self._parser = parser
        self._knowledge = knowledge
        self._repo = document_repo
        # In-memory fallback when no DB repo is available
        self._mem_store: dict[str, ParsedDocument] = {}

    # ------------------------------------------------------------------
    # IDocumentPort
    # ------------------------------------------------------------------

    async def ingest_file(self, path: Path, chunking=None) -> ParsedDocument:
        parsed = self._parser.parse_file(path)
        await self._store(parsed)
        return parsed

    async def ingest_bytes(self, data: bytes, filename: str, chunking=None) -> ParsedDocument:
        parsed = self._parser.parse_bytes(data, filename)
        await self._store(parsed)
        return parsed

    async def get(self, document_id: str) -> ParsedDocument | None:
        """Retrieve a single document by ID."""
        if self._repo is not None:
            try:
                row = await self._repo.get(document_id)
                if row is None:
                    return None
                return ParsedDocument(
                    id=str(row.id),
                    filename=row.original_filename,
                    mime_type=row.mime_type,
                    chunks=[],
                    metadata={
                        "size_bytes": row.size_bytes,
                        "checksum_sha256": row.checksum_sha256,
                        "status": row.status,
                    },
                )
            except Exception as exc:
                logger.warning("DB get failed for '%s': %s — falling back to memory", document_id, exc)
        return self._mem_store.get(document_id)

    async def delete(self, document_id: str) -> None:
        # Remove from vector store
        await self._knowledge.delete(document_id)
        # Remove from SQL store
        if self._repo is not None:
            try:
                await self._repo.delete(document_id)
            except Exception as exc:
                logger.warning("DB delete failed for '%s': %s", document_id, exc)
        else:
            self._mem_store.pop(document_id, None)
        logger.info("Document '%s' deleted", document_id)

    async def list_documents(self, page: int = 0, page_size: int = 20) -> list[ParsedDocument]:
        if self._repo is not None:
            try:
                rows = await self._repo.list_all(limit=page_size)
                return [
                    ParsedDocument(
                        id=str(r.id),
                        filename=r.original_filename,
                        mime_type=r.mime_type,
                        chunks=[],
                        metadata={
                            "size_bytes": r.size_bytes,
                            "checksum_sha256": r.checksum_sha256,
                            "status": r.status,
                        },
                    )
                    for r in rows
                ]
            except Exception as exc:
                logger.warning("DB list failed: %s — using in-memory store", exc)
        return list(self._mem_store.values())

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _store(self, parsed: ParsedDocument) -> None:
        """Store in vector DB and SQL metadata store."""
        # 1. Ingest into ChromaDB
        knowledge_docs = [
            KnowledgeDocument(
                id=f"{parsed.id}__chunk_{i}",
                content=chunk,
                metadata={
                    "document_id": parsed.id,
                    "filename": parsed.filename,
                    "mime_type": parsed.mime_type,
                    "chunk_index": i,
                    **parsed.metadata,
                },
            )
            for i, chunk in enumerate(parsed.chunks)
        ]
        if knowledge_docs:
            await self._knowledge.ingest(knowledge_docs)

        # 2. Persist metadata in SQL (best-effort)
        if self._repo is not None:
            try:
                from backend.infrastructure.database.models import DocumentModel
                import json
                model = DocumentModel(
                    id=parsed.id,
                    filename=parsed.filename,
                    original_filename=parsed.filename,
                    mime_type=parsed.mime_type,
                    size_bytes=parsed.metadata.get("size_bytes", 0),
                    checksum_sha256=parsed.metadata.get("checksum_sha256", ""),
                    storage_path="",
                    status="indexed",
                    owner_id="system",
                    metadata_json=json.dumps(parsed.metadata),
                )
                await self._repo.create(model)
            except Exception as exc:
                logger.warning("DB persist failed for '%s': %s", parsed.filename, exc)
        else:
            self._mem_store[parsed.id] = parsed
        logger.info(
            "Document '%s' ingested — id=%s chunks=%d",
            parsed.filename,
            parsed.id,
            len(parsed.chunks),
        )
