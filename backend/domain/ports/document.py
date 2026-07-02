"""Port: Document Engine."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ParsedDocument:
    id: str
    filename: str
    mime_type: str
    chunks: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


class IDocumentPort(ABC):
    """Contract for document ingestion and parsing."""

    @abstractmethod
    async def ingest_file(self, path: Path) -> ParsedDocument: ...

    @abstractmethod
    async def ingest_bytes(self, data: bytes, filename: str) -> ParsedDocument: ...

    @abstractmethod
    async def delete(self, document_id: str) -> None: ...

    @abstractmethod
    async def list_documents(self) -> list[ParsedDocument]: ...
