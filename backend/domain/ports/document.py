"""Port: Document Engine."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path


class DocumentStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"


@dataclass
class ParsedDocument:
    id: str
    filename: str
    mime_type: str
    chunks: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    status: DocumentStatus = DocumentStatus.PENDING
    error: str | None = None
    char_count: int = 0
    chunk_count: int = 0


@dataclass
class ChunkingConfig:
    chunk_size: int = 512
    chunk_overlap: int = 64
    separator: str = "\n\n"


class IDocumentPort(ABC):
    """Contract for document ingestion and parsing."""

    @abstractmethod
    async def ingest_file(
        self, path: Path, chunking: ChunkingConfig | None = None
    ) -> ParsedDocument: ...

    @abstractmethod
    async def ingest_bytes(
        self, data: bytes, filename: str, chunking: ChunkingConfig | None = None
    ) -> ParsedDocument: ...

    @abstractmethod
    async def delete(self, document_id: str) -> None: ...

    @abstractmethod
    async def list_documents(
        self, page: int = 0, page_size: int = 20
    ) -> list[ParsedDocument]: ...

    @abstractmethod
    async def get(self, document_id: str) -> ParsedDocument | None: ...
