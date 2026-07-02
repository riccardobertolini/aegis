"""Memory engine REST API."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from backend.domain.ports.memory import MemoryEntry, MemoryRole

router = APIRouter(prefix="/api/v1/memory", tags=["memory"])


def _get_memory_service():
    raise HTTPException(status_code=503, detail="MemoryService not initialised")


class TurnIn(BaseModel):
    session_id: str = Field(..., min_length=1)
    role: str = Field("user", pattern="^(user|assistant|system)$")
    content: str = Field(..., min_length=1, max_length=16384)
    intent: str | None = None
    metadata: dict = Field(default_factory=dict)


class TurnOut(BaseModel):
    session_id: str
    role: str
    content: str
    intent: str | None
    timestamp: str
    metadata: dict


class SummaryOut(BaseModel):
    session_id: str
    summary: str
    turn_count: int


@router.post("/turns", status_code=201)
async def append_turn(body: TurnIn, svc=Depends(_get_memory_service)):
    await svc.append(
        MemoryEntry(
            session_id=body.session_id,
            role=MemoryRole(body.role),
            content=body.content,
            intent=body.intent,
            metadata=body.metadata,
        )
    )
    return {"ok": True}


@router.get("/sessions/{session_id}/history", response_model=list[TurnOut])
async def get_history(
    session_id: str,
    last_n: int = Query(20, ge=1, le=200),
    svc=Depends(_get_memory_service),
):
    entries = await svc.get_history(session_id, last_n)
    return [
        TurnOut(
            session_id=e.session_id,
            role=e.role.value,
            content=e.content,
            intent=e.intent,
            timestamp=e.timestamp.isoformat(),
            metadata=e.metadata,
        )
        for e in entries
    ]


@router.delete("/sessions/{session_id}", status_code=204)
async def clear_session(session_id: str, svc=Depends(_get_memory_service)):
    await svc.clear_session(session_id)


@router.post("/sessions/{session_id}/summarize", response_model=SummaryOut)
async def summarize_session(session_id: str, svc=Depends(_get_memory_service)):
    summary = await svc.summarize_session(session_id)
    rec = await svc.get_summary(session_id)
    return SummaryOut(
        session_id=session_id,
        summary=summary,
        turn_count=rec.turn_count if rec else 0,
    )


@router.get("/sessions/{session_id}/summary", response_model=SummaryOut)
async def get_summary(session_id: str, svc=Depends(_get_memory_service)):
    rec = await svc.get_summary(session_id)
    if not rec:
        raise HTTPException(status_code=404, detail="No summary found for this session")
    return SummaryOut(
        session_id=rec.session_id,
        summary=rec.summary,
        turn_count=rec.turn_count,
    )


@router.get("/sessions", response_model=list[str])
async def list_sessions(
    page: int = Query(0, ge=0),
    page_size: int = Query(20, ge=1, le=100),
    svc=Depends(_get_memory_service),
):
    return await svc.list_sessions(page=page, page_size=page_size)
