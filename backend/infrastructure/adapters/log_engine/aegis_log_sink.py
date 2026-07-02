"""AegisLogSink — structlog processor that forwards to LogEngine.

Drop this into the structlog chain to persist system logs into DuckDB,
making them queryable via the Log Engine API.

Usage (in shared/logging.py initialisation):

    from backend.infrastructure.adapters.log_engine.aegis_log_sink import AegisLogSink
    sink = AegisLogSink()  # lazy-init LogEngine
    # add as final processor before the JSON renderer
"""
from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

from backend.domain.ports.log_engine import LogEntry
from backend.shared.logging import get_logger

logger = get_logger(__name__)


class AegisLogSink:
    """Structlog processor that feeds log entries into LogEngine."""

    def __init__(self) -> None:
        self._engine: Any = None  # lazy import to avoid circular deps

    def _get_engine(self):
        if self._engine is None:
            from backend.infrastructure.adapters.log_engine import LogEngine
            self._engine = LogEngine()
        return self._engine

    def __call__(self, logger_obj: Any, method: str, event_dict: dict) -> dict:
        """Called synchronously by structlog. Fire-and-forget async ingest."""
        try:
            entry = LogEntry(
                timestamp=datetime.utcnow(),
                level=method.upper(),
                message=str(event_dict.get("event", "")),
                source=event_dict.get("_record", {}).get("name", "aegis") if isinstance(event_dict.get("_record"), dict) else "aegis",
                context={k: v for k, v in event_dict.items()
                         if k not in {"event", "level", "timestamp", "_record"}},
            )
            eng = self._get_engine()
            # schedule coroutine on running loop if available
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(eng.ingest(entry))
            except RuntimeError:
                pass  # no running loop (e.g. startup) — skip
        except Exception:
            pass  # never raise from a log processor
        return event_dict
