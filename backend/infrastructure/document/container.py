"""DI factory for the Document + RAG subsystem."""
from __future__ import annotations

from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.ports.inference import IInferencePort
from backend.infrastructure.document.db_store import DocumentDBStore
from backend.infrastructure.document.document_service import DocumentService
from backend.infrastructure.document.embedder import build_embedder
from backend.infrastructure.document.knowledge_service import KnowledgeService
from backend.infrastructure.document.rag_pipeline import RAGPipeline
from backend.infrastructure.document.vector_store import ChromaVectorStore


@dataclass_like = None  # Not a dataclass — plain class for IDE clarity


class DocumentContainer:
    def __init__(
        self,
        document_service: DocumentService,
        knowledge_service: KnowledgeService,
        rag_pipeline: RAGPipeline,
    ):
        self.document_service = document_service
        self.knowledge_service = knowledge_service
        self.rag_pipeline = rag_pipeline


def build_document_container(
    session: AsyncSession,
    inference: IInferencePort,
    chroma_dir: Path,
    embedding_model_path: str | Path | None = None,
    collection_name: str = "aegis_rag",
) -> DocumentContainer:
    embedder = build_embedder(embedding_model_path)
    vector_store = ChromaVectorStore(chroma_dir, collection_name)
    db_store = DocumentDBStore(session)

    doc_service = DocumentService(db_store, vector_store, embedder)
    knowledge_service = KnowledgeService(vector_store, embedder)
    rag_pipeline = RAGPipeline(knowledge_service, inference)

    return DocumentContainer(
        document_service=doc_service,
        knowledge_service=knowledge_service,
        rag_pipeline=rag_pipeline,
    )
