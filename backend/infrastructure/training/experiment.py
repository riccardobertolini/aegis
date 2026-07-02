"""Local experiment tracker — no MLflow, no W&B, no cloud.

Stores metrics as append-only JSONL files in experiments/<run_id>/.
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    step: int
    epoch: int
    loss: float
    lr: float
    elapsed_s: float
    extra: dict = field(default_factory=dict)


@dataclass
class RunSummary:
    run_id: str
    job_id: str
    base_model_id: str
    output_model_id: str
    status: str           # "running" | "completed" | "failed"
    started_at: float
    finished_at: float | None
    best_loss: float | None
    total_steps: int
    config: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


class ExperimentTracker:
    """Write-once, append-only local experiment store.

    Layout::

        experiments/
            <run_id>/
                summary.json
                metrics.jsonl
    """

    def __init__(self, experiments_root: str | Path) -> None:
        self._root = Path(experiments_root)
        self._root.mkdir(parents=True, exist_ok=True)
        self._active: dict[str, RunSummary] = {}
        self._start_times: dict[str, float] = {}

    # ------------------------------------------------------------------
    # Run lifecycle
    # ------------------------------------------------------------------

    def start_run(self, run_id: str, job_id: str, config: dict) -> RunSummary:
        run_dir = self._run_dir(run_id)
        run_dir.mkdir(parents=True, exist_ok=True)
        now = time.time()
        summary = RunSummary(
            run_id=run_id,
            job_id=job_id,
            base_model_id=config.get("base_model_id", ""),
            output_model_id=config.get("output_model_id", ""),
            status="running",
            started_at=now,
            finished_at=None,
            best_loss=None,
            total_steps=0,
            config=config,
        )
        self._active[run_id] = summary
        self._start_times[run_id] = now
        self._write_summary(summary)
        logger.info("Experiment run '%s' started", run_id)
        return summary

    def log_metric(self, run_id: str, point: MetricPoint) -> None:
        metrics_path = self._run_dir(run_id) / "metrics.jsonl"
        with open(metrics_path, "a") as f:
            f.write(json.dumps(asdict(point)) + "\n")

        # Update summary
        summary = self._active.get(run_id)
        if summary:
            summary.total_steps = point.step
            if summary.best_loss is None or point.loss < summary.best_loss:
                summary.best_loss = point.loss

    def finish_run(self, run_id: str, status: str = "completed") -> None:
        summary = self._active.pop(run_id, None)
        if summary is None:
            # Load from disk
            summary = self._load_summary(run_id)
        if summary:
            summary.status = status
            summary.finished_at = time.time()
            self._write_summary(summary)
        logger.info("Experiment run '%s' finished — status=%s", run_id, status)

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def list_runs(self) -> list[RunSummary]:
        summaries: list[RunSummary] = []
        for run_dir in sorted(self._root.iterdir()):
            s = self._load_summary(run_dir.name)
            if s:
                summaries.append(s)
        return summaries

    def get_run(self, run_id: str) -> RunSummary | None:
        if run_id in self._active:
            return self._active[run_id]
        return self._load_summary(run_id)

    def get_metrics(self, run_id: str) -> list[MetricPoint]:
        metrics_path = self._run_dir(run_id) / "metrics.jsonl"
        if not metrics_path.exists():
            return []
        points: list[MetricPoint] = []
        with open(metrics_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    d = json.loads(line)
                    points.append(MetricPoint(**d))
        return points

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _run_dir(self, run_id: str) -> Path:
        return self._root / run_id

    def _write_summary(self, summary: RunSummary) -> None:
        path = self._run_dir(summary.run_id) / "summary.json"
        with open(path, "w") as f:
            json.dump(summary.to_dict(), f, indent=2)

    def _load_summary(self, run_id: str) -> RunSummary | None:
        path = self._run_dir(run_id) / "summary.json"
        if not path.exists():
            return None
        try:
            with open(path) as f:
                d = json.load(f)
            return RunSummary(**d)
        except Exception as exc:
            logger.warning("Cannot load summary for run '%s': %s", run_id, exc)
            return None
