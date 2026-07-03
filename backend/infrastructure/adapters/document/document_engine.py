"""DocumentEngine: orchestrates parsing + chunking, implements IDocumentPort."""
from __future__ import annotations

from pathlib import Path

from backend.domain.ports.document import (
    ChunkingConfig,
    IDocumentPort,
    ParsedDocument,
)
from backend.shared.logging import get_logger

from .chunker import chunk_text
from .models import ParsedDocument as InternalParsedDocument
from .models import TextChunk
from .parser_registry import ParserRegistry

logger = get_logger(__name__)

# In-memory store for documents registered via ingest_file / ingest_bytes
_DOCUMENT_STORE: dict[str, ParsedDocument] = {}


class DocumentEngine(IDocumentPort):
    """
    Concrete implementation of IDocumentPort.

    Responsibilities:
    - Accept a file path.
    - Parse via ParserRegistry.
    - Chunk the result.
    - Return ParsedDocument + list[TextChunk].
    """

    def __init__(
        self,
        chunk_size: int = 512,
        overlap: int = 64,
        dedup: bool = True,
    ) -> None:
        self._registry = ParserRegistry()
        self._chunk_size = chunk_size
        self._overlap = overlap
        self._dedup = dedup

    # ------------------------------------------------------------------ #
    # Core synchronous method (used internally by KnowledgeEngine)        #
    # ------------------------------------------------------------------ #

    def ingest(self, path: str | Path) -> tuple[InternalParsedDocument, list[TextChunk]]:
        """Parse and chunk a document file.

        Returns:
            (ParsedDocument, list[TextChunk]) — full doc metadata + ready-to-embed chunks.
        """
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Document not found: {p}")
        if not self._registry.supports(p):
            raise ValueError(f"Unsupported file format: {p.suffix}")

        logger.info("document.ingest.start", path=str(p), format=p.suffix)
        doc = self._registry.parse(p)
        chunks = chunk_text(doc, self._chunk_size, self._overlap, self._dedup)
        logger.info(
            "document.ingest.done",
            path=str(p),
            words=doc.word_count,
            chunks=len(chunks),
        )
        return doc, chunks

    def supports(self, path: str | Path) -> bool:
        """Return True if the file extension is handled."""
        return self._registry.supports(Path(path))

    # ------------------------------------------------------------------ #
    # IDocumentPort — required async interface methods                    #
    # ------------------------------------------------------------------ #

    async def ingest_file(
        self, path: Path, chunking: ChunkingConfig | None = None
    ) -> ParsedDocument:
        """IDocumentPort.ingest_file — delegates to synchronous ingest()."""
        import uuid

        from backend.domain.ports.document import DocumentStatus

        cfg = chunking or ChunkingConfig()
        orig_size, orig_overlap = self._chunk_size, self._overlap
        self._chunk_size, self._overlap = cfg.chunk_size, cfg.chunk_overlap
        try:
            doc, chunks = self.ingest(path)
        finally:
            self._chunk_size, self._overlap = orig_size, orig_overlap

        pd = ParsedDocument(
            id=str(uuid.uuid4()),
            filename=path.name,
            mime_type=f"application/{path.suffix.lstrip('.')}",
            chunks=[c.text for c in chunks],
            char_count=doc.char_count,
            chunk_count=len(chunks),
            status=DocumentStatus.READY,
        )
        _DOCUMENT_STORE[pd.id] = pd
        return pd

    async def ingest_bytes(
        self, data: bytes, filename: str, chunking: ChunkingConfig | None = None
    ) -> ParsedDocument:
        """IDocumentPort.ingest_bytes — write to a temp file then delegate."""
        import tempfile
        from pathlib import Path as _Path


        suffix = _Path(filename).suffix or ".bin"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(data)
            tmp_path = _Path(tmp.name)
        try:
            return await self.ingest_file(tmp_path, chunking)
        finally:
            tmp_path.unlink(missing_ok=True)

    async def delete(self, document_id: str) -> None:
        """IDocumentPort.delete — removes a document from the in-memory store."""
        _DOCUMENT_STORE.pop(document_id, None)
        logger.info("document.deleted", document_id=document_id)

    async def list_documents(
        self, page: int = 0, page_size: int = 20
    ) -> list[ParsedDocument]:
        """IDocumentPort.list_documents — returns paginated documents."""
        docs = list(_DOCUMENT_STORE.values())
        start = page * page_size
        return docs[start : start + page_size]

    async def get(self, document_id: str) -> ParsedDocument | None:
        """IDocumentPort.get — returns a document by id, or None."""
        return _DOCUMENT_STORE.get(document_id)
