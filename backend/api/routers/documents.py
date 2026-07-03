"""REST endpoints for the Document Engine."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.infrastructure.adapters.document.document_engine import DocumentEngine

router = APIRouter(prefix="/documents", tags=["documents"])
_engine = DocumentEngine()


class IngestRequest(BaseModel):
    path: str


class IngestResponse(BaseModel):
    source_path: str
    format: str
    title: str
    word_count: int
    chunk_count: int
    content_hash: str


@router.post("/ingest", response_model=IngestResponse)
def ingest_document(req: IngestRequest) -> IngestResponse:
    """Parse and chunk a document. Returns metadata + chunk count."""
    try:
        doc, chunks = _engine.ingest(req.path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return IngestResponse(
        source_path=doc.source_path,
        format=doc.format.value,
        title=doc.title,
        word_count=doc.word_count,
        chunk_count=len(chunks),
        content_hash=doc.content_hash,
    )


@router.get("/formats")
def supported_formats() -> dict:
    """List all supported document formats."""
    from backend.infrastructure.adapters.document.models import FORMAT_EXTENSIONS
    return {"extensions": sorted(FORMAT_EXTENSIONS.keys())}
