"""Port: Knowledge / RAG Engine."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class Document:
    id: str
    content: str
    metadata: dict = field(default_factory=dict)


@dataclass
class SearchQuery:
    text: str
    top_k: int = 5
    filters: dict = field(default_factory=dict)


@dataclass
class SearchResult:
    document: Document
    score: float


class IKnowledgePort(ABC):
    """Contract for local RAG / vector knowledge base."""

    @abstractmethod
    async def ingest(self, documents: list[Document]) -> None: ...

    @abstractmethod
    async def search(self, query: SearchQuery) -> list[SearchResult]: ...

    @abstractmethod
    async def delete(self, document_id: str) -> None: ...

    @abstractmethod
    async def list_documents(self, page: int = 0, page_size: int = 20) -> list[Document]: ...
