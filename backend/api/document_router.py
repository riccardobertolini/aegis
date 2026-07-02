"""Document + RAG REST API."""
from __future__ import annotations

import json
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/documents", tags=["documents", "rag"])


# ── Dependency stubs (replaced by DI in main.py) ───────────────────────────────

def _get_doc_service():
    raise HTTPException(status_code=503, detail="DocumentService not initialised")

def _get_rag_pipeline():
    raise HTTPException(status_code=503, detail="RAGPipeline not initialised")

def _get_knowledge_service():
    raise HTTPException(status_code=503, detail="KnowledgeService not initialised")


# ── Schemas ────────────────────────────────────────────────────────────────────

class DocumentOut(BaseModel):
    id: str
    filename: str
    mime_type: str
    status: str
    char_count: int
    chunk_count: int
    metadata: dict
    error: str | None = None


class RAGQueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4096)
    top_k: int = Field(5, ge=1, le=50)
    model_id: str | None = None
    max_tokens: int = Field(512, ge=1, le=4096)
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    filters: dict = Field(default_factory=dict)
    stream: bool = False


class RAGQueryResponse(BaseModel):
    answer: str
    sources: list[dict]
    model_id: str | None
    retrieved_chunks: int


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(5, ge=1, le=100)
    filters: dict = Field(default_factory=dict)


# ── Document endpoints ─────────────────────────────────────────────────────────

@router.post("/upload", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    chunk_size: int = Query(512, ge=64, le=4096),
    chunk_overlap: int = Query(64, ge=0, le=512),
    doc_service=Depends(_get_doc_service),
):
    """Upload and ingest a document (parse → chunk → embed → store)."""
    from backend.domain.ports.document import ChunkingConfig
    data = await file.read()
    cfg = ChunkingConfig(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    doc = await doc_service.ingest_bytes(data, file.filename or "upload", cfg)
    return DocumentOut(
        id=doc.id,
        filename=doc.filename,
        mime_type=doc.mime_type,
        status=doc.status.value,
        char_count=doc.char_count,
        chunk_count=doc.chunk_count,
        metadata=doc.metadata,
        error=doc.error,
    )


@router.get("/", response_model=list[DocumentOut])
async def list_documents(
    page: int = Query(0, ge=0),
    page_size: int = Query(20, ge=1, le=100),
    doc_service=Depends(_get_doc_service),
):
    docs = await doc_service.list_documents(page=page, page_size=page_size)
    return [
        DocumentOut(
            id=d.id,
            filename=d.filename,
            mime_type=d.mime_type,
            status=d.status.value,
            char_count=d.char_count,
            chunk_count=d.chunk_count,
            metadata=d.metadata,
            error=d.error,
        )
        for d in docs
    ]


@router.get("/{document_id}", response_model=DocumentOut)
async def get_document(
    document_id: str,
    doc_service=Depends(_get_doc_service),
):
    doc = await doc_service.get(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentOut(
        id=doc.id,
        filename=doc.filename,
        mime_type=doc.mime_type,
        status=doc.status.value,
        char_count=doc.char_count,
        chunk_count=doc.chunk_count,
        metadata=doc.metadata,
        error=doc.error,
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    doc_service=Depends(_get_doc_service),
):
    await doc_service.delete(document_id)


# ── Knowledge / search endpoint ────────────────────────────────────────────────

@router.post("/search", response_model=list[dict])
async def semantic_search(
    req: SearchRequest,
    knowledge_service=Depends(_get_knowledge_service),
):
    """Semantic search over the embedded knowledge base."""
    from backend.domain.ports.knowledge import SearchQuery
    results = await knowledge_service.search(
        SearchQuery(text=req.query, top_k=req.top_k, filters=req.filters)
    )
    return [
        {
            "doc_id": r.document.id,
            "score": r.score,
            "excerpt": r.document.content[:300],
            "metadata": r.document.metadata,
        }
        for r in results
    ]


# ── RAG endpoints ──────────────────────────────────────────────────────────────

@router.post("/rag/query", response_model=RAGQueryResponse)
async def rag_query(
    req: RAGQueryRequest,
    rag=Depends(_get_rag_pipeline),
):
    """Retrieve-then-generate: answer a question grounded in local documents."""
    from backend.infrastructure.document.rag_pipeline import RAGRequest
    if req.stream:
        raise HTTPException(
            status_code=400,
            detail="Use /rag/stream for streaming responses.",
        )
    result = await rag.run(
        RAGRequest(
            question=req.question,
            top_k=req.top_k,
            model_id=req.model_id,
            max_tokens=req.max_tokens,
            temperature=req.temperature,
            filters=req.filters,
        )
    )
    return RAGQueryResponse(
        answer=result.answer,
        sources=result.sources,
        model_id=result.model_id,
        retrieved_chunks=result.retrieved_chunks,
    )


@router.post("/rag/stream")
async def rag_stream(
    req: RAGQueryRequest,
    rag=Depends(_get_rag_pipeline),
):
    """SSE streaming RAG response."""
    from backend.infrastructure.document.rag_pipeline import RAGRequest

    async def _event_generator():
        rag_req = RAGRequest(
            question=req.question,
            top_k=req.top_k,
            model_id=req.model_id,
            max_tokens=req.max_tokens,
            temperature=req.temperature,
            filters=req.filters,
        )
        async for token in rag.stream(rag_req):
            yield f"data: {json.dumps({'token': token})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(_event_generator(), media_type="text/event-stream")
