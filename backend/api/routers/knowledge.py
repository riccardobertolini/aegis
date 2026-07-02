"""REST endpoints for the Knowledge Engine (RAG)."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.infrastructure.adapters.knowledge.knowledge_engine import KnowledgeEngine
from backend.infrastructure.adapters.knowledge.models import RagContext

router = APIRouter(prefix="/knowledge", tags=["knowledge"])
_engine = KnowledgeEngine()


class CreateKbRequest(BaseModel):
    name: str
    description: str = ""
    category: str = "general"
    assistant_id: str | None = None


class AddDocumentRequest(BaseModel):
    kb_id: str
    path: str
    force_reindex: bool = False


class RetrieveRequest(BaseModel):
    kb_ids: list[str]
    query: str
    top_k: int = 5
    max_chars: int = 4096


@router.post("/kb")
def create_kb(req: CreateKbRequest) -> dict:
    """Create a new knowledge base."""
    kb = _engine.create_kb(req.name, req.description, req.category, req.assistant_id)
    return kb.model_dump()


@router.get("/kb")
def list_kbs(category: str | None = None, assistant_id: str | None = None) -> list:
    """List knowledge bases, optionally filtered."""
    return [kb.model_dump() for kb in _engine.list_kbs(category, assistant_id)]


@router.delete("/kb/{kb_id}")
def delete_kb(kb_id: str) -> dict:
    try:
        _engine.delete_kb(kb_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"deleted": kb_id}


@router.post("/document")
def add_document(req: AddDocumentRequest) -> dict:
    """Ingest and index a document into a knowledge base."""
    try:
        count = _engine.add_document(req.kb_id, req.path, req.force_reindex)
    except (KeyError, FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"kb_id": req.kb_id, "indexed_chunks": count}


@router.post("/retrieve")
def retrieve(req: RetrieveRequest) -> dict:
    """RAG retrieval: returns context + citations for the query."""
    try:
        ctx: RagContext = _engine.build_rag_context(
            query=req.query,
            kb_ids=req.kb_ids,
            max_chars=req.max_chars,
            top_k=req.top_k,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ctx.model_dump()


@router.get("/kb/{kb_id}/integrity")
def integrity_check(kb_id: str) -> dict:
    """Verify index integrity for a knowledge base."""
    try:
        return _engine.integrity_check(kb_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
