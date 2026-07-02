"""API router — Time Series Engine."""
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from backend.domain.ports.timeseries import Metric, MetricQuery
from backend.infrastructure.adapters.timeseries import TimeSeriesEngine
from backend.shared.config import get_settings

router = APIRouter(prefix="/timeseries", tags=["timeseries"])


def _engine() -> TimeSeriesEngine:
    return TimeSeriesEngine(settings=get_settings())


class RecordBody(BaseModel):
    name: str
    value: float
    timestamp: datetime | None = None
    tags: dict = {}


class QueryBody(BaseModel):
    name: str
    since: datetime
    until: datetime
    aggregation: str = "avg"
    bucket_seconds: int = 60


@router.post("/record", status_code=201)
async def record_metric(
    body: RecordBody,
    engine: TimeSeriesEngine = Depends(_engine),
):
    m = Metric(
        name=body.name,
        value=body.value,
        timestamp=body.timestamp or datetime.utcnow(),
        tags=body.tags,
    )
    await engine.record(m)
    return {"ok": True}


@router.post("/query")
async def query_series(
    body: QueryBody,
    engine: TimeSeriesEngine = Depends(_engine),
):
    q = MetricQuery(
        name=body.name,
        since=body.since,
        until=body.until,
        aggregation=body.aggregation,
        bucket_seconds=body.bucket_seconds,
    )
    series = await engine.query(q)
    anomalies = await engine.detect_anomalies(series)
    slope = await engine.trend_slope(series)
    return {
        "name": series.name,
        "points": [{"ts": ts.isoformat(), "value": v} for ts, v in series.points],
        "anomalies": [{"ts": ts.isoformat(), "value": v, "z_score": z} for ts, v, z in anomalies],
        "trend_slope": slope,
    }


@router.get("/metrics")
async def list_metrics(engine: TimeSeriesEngine = Depends(_engine)):
    return {"metrics": await engine.list_metrics()}
