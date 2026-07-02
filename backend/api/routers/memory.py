"""API router — Memory Engine."""
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from backend.domain.ports.memory import MemoryEntry
from backend.infrastructure.adapters.memory import MemoryEngine
from backend.shared.config import get_settings

router = APIRouter(prefix="/memory", tags=["memory"])


def _engine() -> MemoryEngine:
    return MemoryEngine(settings=get_settings())


class AppendRequest(BaseModel):
    session_id: str
    role: str
    content: str
    metadata: dict = {}


class SummaryResponse(BaseModel):
    session_id: str
    summary: str


@router.post("/sessions/{session_id}/entries", status_code=201)
async def append_entry(
    session_id: str,
    body: AppendRequest,
    engine: MemoryEngine = Depends(_engine),
):
    """Append a conversation entry to a session."""
    entry = MemoryEntry(
        session_id=session_id,
        role=body.role,
        content=body.content,
        metadata=body.metadata,
    )
    await engine.append(entry)
    return {"ok": True}


@router.get("/sessions/{session_id}/history")
async def get_history(
    session_id: str,
    last_n: int = Query(20, ge=1, le=200),
    engine: MemoryEngine = Depends(_engine),
):
    entries = await engine.get_history(session_id, last_n=last_n)
    return [{"role": e.role, "content": e.content, "ts": e.timestamp.isoformat()} for e in entries]


@router.post("/sessions/{session_id}/summarize")
async def summarize(
    session_id: str,
    engine: MemoryEngine = Depends(_engine),
) -> SummaryResponse:
    summary = await engine.summarize_session(session_id)
    return SummaryResponse(session_id=session_id, summary=summary)


@router.delete("/sessions/{session_id}", status_code=204)
async def clear_session(
    session_id: str,
    engine: MemoryEngine = Depends(_engine),
):
    await engine.clear_session(session_id)


@router.get("/sessions")
async def list_sessions(
    assistant_id: str | None = Query(None),
    engine: MemoryEngine = Depends(_engine),
):
    sessions = await engine.list_sessions(assistant_id=assistant_id)
    return {"sessions": sessions}
