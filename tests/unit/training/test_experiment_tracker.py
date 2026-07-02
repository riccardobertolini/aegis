"""Unit tests — ExperimentTracker."""
from datetime import datetime, timezone
from pathlib import Path

import pytest

from backend.domain.ports.training import ExperimentMetrics
from backend.infrastructure.training.experiment_tracker import ExperimentTracker


def test_init_and_log(tmp_path):
    tracker = ExperimentTracker(tmp_path)
    tracker.init_experiment("job1", {"lr": 1e-4, "epochs": 3})
    m = ExperimentMetrics(
        job_id="job1", step=1, epoch=0,
        train_loss=2.5, val_loss=2.8,
        learning_rate=1e-4, tokens_per_second=120.0,
        timestamp=datetime.now(timezone.utc),
    )
    tracker.log_metrics(m)
    rows = tracker.read_metrics("job1")
    assert len(rows) == 1
    assert abs(rows[0].train_loss - 2.5) < 1e-6


def test_multiple_steps(tmp_path):
    tracker = ExperimentTracker(tmp_path)
    tracker.init_experiment("job2", {})
    for i in range(5):
        tracker.log_metrics(ExperimentMetrics(
            job_id="job2", step=i, epoch=0,
            train_loss=float(i), timestamp=datetime.now(timezone.utc),
        ))
    rows = tracker.read_metrics("job2")
    assert len(rows) == 5


def test_summary(tmp_path):
    tracker = ExperimentTracker(tmp_path)
    tracker.init_experiment("job3", {})
    tracker.write_summary("job3", {"best_val_loss": 1.23})
    summary_path = tmp_path / "job3" / "summary.json"
    assert summary_path.exists()
