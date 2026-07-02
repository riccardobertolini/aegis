"""Port: TimeSeries Engine."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Metric:
    name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tags: dict = field(default_factory=dict)


@dataclass
class MetricQuery:
    name: str
    since: datetime
    until: datetime
    aggregation: str = "avg"  # avg | sum | min | max | count
    bucket_seconds: int = 60


@dataclass
class MetricSeries:
    name: str
    points: list[tuple[datetime, float]]


class ITimeSeriesPort(ABC):
    """Contract for local metrics collection and query."""

    @abstractmethod
    async def record(self, metric: Metric) -> None: ...

    @abstractmethod
    async def query(self, q: MetricQuery) -> MetricSeries: ...
