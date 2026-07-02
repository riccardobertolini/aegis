"""API router — Log Engine."""
from datetime import datetime

from fastapi import APIRouter, Depends, Query, UploadFile, File
from pydantic import BaseModel

from backend.domain.ports.log_engine import LogEntry, LogQuery
from backend.infrastructure.adapters.log_engine import LogEngine
from backend.shared.config import get_settings

router = APIRouter(prefix="/logs", tags=["logs"])


def _engine() -> LogEngine:
    return LogEngine(settings=get_settings())


@router.get("/tail")
async def tail_logs(
    n: int = Query(50, ge=1, le=1000),
    engine: LogEngine = Depends(_engine),
):
    entries = await engine.tail(n)
    return [
        {
            "ts": e.timestamp.isoformat(),
            "level": e.level,
            "source": e.source,
            "message": e.message,
            "context": e.context,
        }
        for e in entries
    ]


@router.get("/query")
async def query_logs(
    level: str | None = Query(None),
    source: str | None = Query(None),
    since: datetime | None = Query(None),
    until: datetime | None = Query(None),
    limit: int = Query(100, ge=1, le=5000),
    engine: LogEngine = Depends(_engine),
):
    q = LogQuery(level=level, source=source, since=since, until=until, limit=limit)
    entries = await engine.query(q)
    return [
        {
            "ts": e.timestamp.isoformat(),
            "level": e.level,
            "source": e.source,
            "message": e.message,
        }
        for e in entries
    ]


@router.get("/histogram")
async def severity_histogram(engine: LogEngine = Depends(_engine)):
    return await engine.severity_histogram()


@router.get("/top-sources")
async def top_sources(
    n: int = Query(10, ge=1, le=100),
    engine: LogEngine = Depends(_engine),
):
    sources = await engine.top_sources(n)
    return [{"source": s, "count": c} for s, c in sources]


@router.get("/patterns")
async def detect_patterns(engine: LogEngine = Depends(_engine)):
    return await engine.detect_patterns()
