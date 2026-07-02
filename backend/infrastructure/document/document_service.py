"""DocumentService — implements IDocumentPort."""
from __future__ import annotations

import asyncio
import json
import uuid
from functools import partial
from pathlib import Path

from backend.domain.ports.document import (
    ChunkingConfig,
    DocumentStatus,
    IDocumentPort,
    ParsedDocument,
)
from backend.infrastructure.document.chunker import TextChunker
from backend.infrastructure.document.db_store import DocumentDBStore, DocumentRecord
from backend.infrastructure.document.embedder import IEmbedder
from backend.infrastructure.document.parsers import detect_mime, get_parser
from backend.infrastructure.document.vector_store import ChromaVectorStore


class DocumentService(IDocumentPort):
    """Orchestrates parse → chunk → embed → store for every document."""

    def __init__(
        self,
        db_store: DocumentDBStore,
        vector_store: ChromaVectorStore,
        embedder: IEmbedder,
        default_chunking: ChunkingConfig | None = None,
    ):
        self._db = db_store
        self._vs = vector_store
        self._embedder = embedder
        self._default_chunking = default_chunking or ChunkingConfig()

    # ── IDocumentPort ──────────────────────────────────────────────────────────

    async def ingest_file(
        self, path: Path, chunking: ChunkingConfig | None = None
    ) -> ParsedDocument:
        data = path.read_bytes()
        return await self.ingest_bytes(data, path.name, chunking)

    async def ingest_bytes(
        self, data: bytes, filename: str, chunking: ChunkingConfig | None = None
    ) -> ParsedDocument:
        doc_id = str(uuid.uuid4())
        mime = detect_mime(filename)
        cfg = chunking or self._default_chunking

        record = DocumentRecord(
            id=doc_id,
            filename=filename,
            mime_type=mime,
            status=DocumentStatus.PROCESSING,
        )
        await self._db.upsert(record)

        try:
            parser = get_parser(mime)
            if parser is None:
                raise ValueError(f"No parser available for MIME type: {mime}")

            loop = asyncio.get_event_loop()
            parse_result = await loop.run_in_executor(
                None, partial(parser.parse, data, filename)
            )

            chunker = TextChunker(cfg)
            chunks = await loop.run_in_executor(None, chunker.split, parse_result.text)

            embeddings = await loop.run_in_executor(
                None, self._embedder.embed, chunks
            )

            meta = {**parse_result.metadata, "filename": filename, "mime": mime}
            self._vs.upsert(doc_id, chunks, embeddings, meta)

            record.status = DocumentStatus.READY
            record.char_count = len(parse_result.text)
            record.chunk_count = len(chunks)
            record.metadata_json = json.dumps(meta)
            await self._db.upsert(record)

            return ParsedDocument(
                id=doc_id,
                filename=filename,
                mime_type=mime,
                chunks=chunks,
                metadata=meta,
                status=DocumentStatus.READY,
                char_count=record.char_count,
                chunk_count=record.chunk_count,
            )

        except Exception as exc:
            record.status = DocumentStatus.ERROR
            record.error = str(exc)
            await self._db.upsert(record)
            raise

    async def delete(self, document_id: str) -> None:
        self._vs.delete_by_doc_id(document_id)
        await self._db.delete(document_id)

    async def list_documents(
        self, page: int = 0, page_size: int = 20
    ) -> list[ParsedDocument]:
        records = await self._db.list_page(page, page_size)
        return [self._to_domain(r) for r in records]

    async def get(self, document_id: str) -> ParsedDocument | None:
        rec = await self._db.get(document_id)
        return self._to_domain(rec) if rec else None

    # ── helpers ────────────────────────────────────────────────────────────────

    @staticmethod
    def _to_domain(rec: DocumentRecord) -> ParsedDocument:
        return ParsedDocument(
            id=rec.id,
            filename=rec.filename,
            mime_type=rec.mime_type,
            status=DocumentStatus(rec.status),
            error=rec.error,
            char_count=rec.char_count,
            chunk_count=rec.chunk_count,
            metadata=json.loads(rec.metadata_json or "{}"),
        )
