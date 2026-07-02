"""DocumentContainer — DI factory for the Document + RAG stack."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from backend.infrastructure.rag.parser import DocumentParser
from backend.infrastructure.rag.chunker import TextChunker
from backend.infrastructure.rag.embedder import LocalEmbedder
from backend.infrastructure.rag.chroma_adapter import ChromaKnowledgeAdapter
from backend.infrastructure.rag.document_service import DocumentService
from backend.infrastructure.rag.rag_service import RAGService
from backend.domain.ports.document import IDocumentPort
from backend.domain.ports.knowledge import IKnowledgePort
from backend.domain.ports.inference import IInferencePort


class DocumentContainer:
    """Wires DocumentParser → Chunker → Embedder → Chroma → DocumentService + RAGService.

    Usage::

        container = DocumentContainer.build(settings, inference_port)
        document_port: IDocumentPort = container.document_service
        knowledge_port: IKnowledgePort = container.knowledge
        rag: RAGService = container.rag_service
    """

    def __init__(
        self,
        parser: DocumentParser,
        chunker: TextChunker,
        embedder: LocalEmbedder,
        knowledge: ChromaKnowledgeAdapter,
        document_service: DocumentService,
        rag_service: RAGService,
    ) -> None:
        self._parser = parser
        self._chunker = chunker
        self._embedder = embedder
        self._knowledge = knowledge
        self._document_service = document_service
        self._rag_service = rag_service

    @property
    def document_service(self) -> IDocumentPort:
        return self._document_service

    @property
    def knowledge(self) -> IKnowledgePort:
        return self._knowledge

    @property
    def rag_service(self) -> RAGService:
        return self._rag_service

    @property
    def embedder(self) -> LocalEmbedder:
        return self._embedder

    @classmethod
    def build(
        cls,
        data_dir: str | Path,
        inference: IInferencePort,
        models_root: Optional[str | Path] = None,
        embed_model: str = "all-MiniLM-L6-v2",
        collection_name: str = "aegis_default",
        chunk_size: int = 512,
        chunk_overlap: int = 64,
        default_model_id: str = "",
        document_repo=None,
    ) -> "DocumentContainer":
        """Build a fully wired DocumentContainer.

        Args:
            data_dir:         Base data directory (chroma DB stored here).
            inference:        IInferencePort from InferenceContainer.
            models_root:      Path to models/ dir (embed model lives in models/embed/).
            embed_model:      Name or path of the sentence-transformer model.
            collection_name:  ChromaDB collection name.
            chunk_size:       Characters per chunk.
            chunk_overlap:    Overlap characters between consecutive chunks.
            default_model_id: Default LLM model for RAG generation.
            document_repo:    Optional SQLiteDocumentRepository for metadata persistence.
        """
        data_path = Path(data_dir)
        chroma_dir = str(data_path / "chroma")

        parser = DocumentParser()
        chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        embedder = LocalEmbedder(
            model_name_or_path=embed_model,
            models_root=models_root,
        )
        knowledge = ChromaKnowledgeAdapter(
            persist_dir=chroma_dir,
            embedder=embedder,
            chunker=chunker,
            collection_name=collection_name,
        )
        document_service = DocumentService(
            parser=parser,
            knowledge=knowledge,
            document_repo=document_repo,
        )
        rag_service = RAGService(
            knowledge=knowledge,
            inference=inference,
            default_model_id=default_model_id,
        )
        return cls(
            parser=parser,
            chunker=chunker,
            embedder=embedder,
            knowledge=knowledge,
            document_service=document_service,
            rag_service=rag_service,
        )
