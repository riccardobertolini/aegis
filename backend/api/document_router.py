"""REST API router for Document ingestion and RAG queries.

Endpoints:
    POST   /api/v1/documents/upload          — multipart file upload + ingest
    GET    /api/v1/documents                 — list all documents
    GET    /api/v1/documents/{doc_id}        — get document metadata
    DELETE /api/v1/documents/{doc_id}        — delete document + vectors
    POST   /api/v1/documents/search          — RAG query (retrieve + generate)
    POST   /api/v1/knowledge/ingest          — ingest raw text documents
    GET    /api/v1/knowledge/documents       — list knowledge-base docs
    DELETE /api/v1/knowledge/documents/{id}  — delete from vector store
    POST   /api/v1/knowledge/search          — vector similarity search only
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, status
from pydantic import BaseModel, Field

from backend.infrastructure.rag.rag_service import RAGRequest

logger = logging.getLogger(__name__)

doc_router = APIRouter()
knowledge_router = APIRouter()


# ---------------------------------------------------------------------------
# Dependency
# ---------------------------------------------------------------------------

def _get_doc_container(request: Request):
    container = getattr(request.app.state, "document_container", None)
    if container is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Document engine not initialised.",
        )
    return container


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class DocumentOut(BaseModel):
    id: str
    filename: str
    mime_type: str
    chunk_count: int
    metadata: dict


class RAGQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=4096)
    model_id: str = Field(default="")
    top_k: int = Field(default=5, ge=1, le=20)
    max_tokens: int = Field(default=512, ge=1, le=4096)
    temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    knowledge_base_id: str = Field(default="")
    include_sources: bool = Field(default=True)
    filters: dict = Field(default_factory=dict)


class RAGQueryResponse(BaseModel):
    answer: str
    sources: list[dict]
    model_id: str
    prompt_tokens: int
    completion_tokens: int


class IngestRequest(BaseModel):
    documents: list[dict] = Field(..., description="List of {id, content, metadata} objects")


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=50)
    filters: dict = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Document routes
# ---------------------------------------------------------------------------

@doc_router.post(
    "/upload",
    response_model=DocumentOut,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and ingest a document file",
)
async def upload_document(
    file: UploadFile = File(...),
    container=Depends(_get_doc_container),
) -> DocumentOut:
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    try:
        parsed = await container.document_service.ingest_bytes(
            data=data, filename=file.filename or "upload"
        )
    except ValueError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Upload failed for '%s': %s", file.filename, exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return DocumentOut(
        id=parsed.id,
        filename=parsed.filename,
        mime_type=parsed.mime_type,
        chunk_count=len(parsed.chunks),
        metadata=parsed.metadata,
    )


@doc_router.get(
    "",
    response_model=list[DocumentOut],
    summary="List all ingested documents",
)
async def list_documents(
    container=Depends(_get_doc_container),
) -> list[DocumentOut]:
    docs = await container.document_service.list_documents()
    return [
        DocumentOut(
            id=d.id,
            filename=d.filename,
            mime_type=d.mime_type,
            chunk_count=len(d.chunks),
            metadata=d.metadata,
        )
        for d in docs
    ]


@doc_router.delete(
    "/{doc_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a document and its vectors",
)
async def delete_document(
    doc_id: str,
    container=Depends(_get_doc_container),
) -> None:
    await container.document_service.delete(doc_id)


@doc_router.post(
    "/search",
    response_model=RAGQueryResponse,
    summary="RAG query: retrieve context then generate answer",
)
async def rag_search(
    body: RAGQueryRequest,
    container=Depends(_get_doc_container),
) -> RAGQueryResponse:
    rag_req = RAGRequest(
        query=body.query,
        model_id=body.model_id,
        top_k=body.top_k,
        max_tokens=body.max_tokens,
        temperature=body.temperature,
        filters=body.filters,
        knowledge_base_id=body.knowledge_base_id,
        include_sources=body.include_sources,
    )
    try:
        resp = await container.rag_service.query(rag_req)
    except Exception as exc:
        logger.error("RAG query failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return RAGQueryResponse(
        answer=resp.answer,
        sources=[
            {
                "document_id": s.document_id,
                "chunk_text": s.chunk_text[:512],
                "score": round(s.score, 4),
                "metadata": s.metadata,
            }
            for s in resp.sources
        ],
        model_id=resp.model_id,
        prompt_tokens=resp.prompt_tokens,
        completion_tokens=resp.completion_tokens,
    )


# ---------------------------------------------------------------------------
# Knowledge (vector store) routes
# ---------------------------------------------------------------------------

@knowledge_router.post(
    "/ingest",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest raw text documents directly into the vector store",
)
async def ingest_documents(
    body: IngestRequest,
    container=Depends(_get_doc_container),
) -> dict:
    from backend.domain.ports.knowledge import Document
    docs = [
        Document(
            id=d.get("id", ""),
            content=d.get("content", ""),
            metadata=d.get("metadata", {}),
        )
        for d in body.documents
        if d.get("id") and d.get("content")
    ]
    if not docs:
        raise HTTPException(status_code=400, detail="No valid documents provided")
    await container.knowledge.ingest(docs)
    return {"ingested": len(docs)}


@knowledge_router.get(
    "/documents",
    summary="List documents in the vector store",
)
async def list_knowledge_documents(
    page: int = 0,
    page_size: int = 20,
    container=Depends(_get_doc_container),
) -> list[dict]:
    docs = await container.knowledge.list_documents(page=page, page_size=page_size)
    return [
        {"id": d.id, "content_preview": d.content[:200], "metadata": d.metadata}
        for d in docs
    ]


@knowledge_router.delete(
    "/documents/{doc_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a document from the vector store",
)
async def delete_knowledge_document(
    doc_id: str,
    container=Depends(_get_doc_container),
) -> None:
    await container.knowledge.delete(doc_id)


@knowledge_router.post(
    "/search",
    summary="Vector similarity search (no generation)",
)
async def knowledge_search(
    body: KnowledgeSearchRequest,
    container=Depends(_get_doc_container),
) -> list[dict]:
    from backend.domain.ports.knowledge import SearchQuery
    sq = SearchQuery(text=body.query, top_k=body.top_k, filters=body.filters)
    results = await container.knowledge.search(sq)
    return [
        {
            "document_id": r.document.id,
            "content_preview": r.document.content[:300],
            "score": round(r.score, 4),
            "metadata": r.document.metadata,
        }
        for r in results
    ]
