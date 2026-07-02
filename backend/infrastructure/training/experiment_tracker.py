"""Experiment tracker — fully local, JSON-lines per job, no external service."""
from __future__ import annotations

import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path

from backend.domain.ports.training import ExperimentMetrics

logger = logging.getLogger(__name__)


class ExperimentTracker:
    """
    Writes one JSONL metrics file per job under::

        experiments/<job_id>/metrics.jsonl
        experiments/<job_id>/config.json
        experiments/<job_id>/summary.json

    Thread-safe, append-only. No external process or service required.
    """

    def __init__(self, experiments_root: Path) -> None:
        self._root = experiments_root
        self._root.mkdir(parents=True, exist_ok=True)
        self._locks: dict[str, threading.Lock] = {}

    def init_experiment(self, job_id: str, config: dict) -> None:
        job_dir = self._job_dir(job_id)
        job_dir.mkdir(parents=True, exist_ok=True)
        config_path = job_dir / "config.json"
        config_path.write_text(json.dumps(config, indent=2, default=str))
        (job_dir / "metrics.jsonl").touch()
        self._locks[job_id] = threading.Lock()
        logger.info("Experiment '%s' initialised", job_id)

    def log_metrics(self, metrics: ExperimentMetrics) -> None:
        job_id = metrics.job_id
        lock = self._locks.setdefault(job_id, threading.Lock())
        row = {
            "step": metrics.step,
            "epoch": metrics.epoch,
            "train_loss": metrics.train_loss,
            "val_loss": metrics.val_loss,
            "lr": metrics.learning_rate,
            "tok_per_sec": metrics.tokens_per_second,
            "ts": metrics.timestamp.isoformat(),
        }
        with lock:
            path = self._job_dir(job_id) / "metrics.jsonl"
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(row) + "\n")

    def read_metrics(self, job_id: str) -> list[ExperimentMetrics]:
        path = self._job_dir(job_id) / "metrics.jsonl"
        if not path.exists():
            return []
        results: list[ExperimentMetrics] = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                    results.append(
                        ExperimentMetrics(
                            job_id=job_id,
                            step=r["step"],
                            epoch=r["epoch"],
                            train_loss=r["train_loss"],
                            val_loss=r.get("val_loss"),
                            learning_rate=r.get("lr", 0.0),
                            tokens_per_second=r.get("tok_per_sec", 0.0),
                            timestamp=datetime.fromisoformat(r["ts"]),
                        )
                    )
                except Exception as exc:
                    logger.warning("Bad metrics row in %s: %s", job_id, exc)
        return results

    def write_summary(self, job_id: str, summary: dict) -> None:
        path = self._job_dir(job_id) / "summary.json"
        path.write_text(json.dumps(summary, indent=2, default=str))

    def list_experiments(self) -> list[str]:
        return [
            p.name for p in sorted(self._root.iterdir()) if p.is_dir()
        ]

    # ------------------------------------------------------------------
    def _job_dir(self, job_id: str) -> Path:
        return self._root / job_id
