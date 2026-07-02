"""DocumentEngine: orchestrates parsing + chunking, implements IDocumentPort."""
from __future__ import annotations

from pathlib import Path

from backend.domain.ports.document import IDocumentPort
from backend.shared.logging import get_logger

from .chunker import chunk_text
from .models import ParsedDocument, TextChunk
from .parser_registry import ParserRegistry

logger = get_logger(__name__)


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
    # IDocumentPort implementation                                         #
    # ------------------------------------------------------------------ #

    def ingest(self, path: str | Path) -> tuple[ParsedDocument, list[TextChunk]]:
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
