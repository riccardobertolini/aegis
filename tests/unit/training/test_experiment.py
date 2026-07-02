"""Unit tests for ExperimentTracker."""
import pytest
from backend.infrastructure.training.experiment import ExperimentTracker, MetricPoint


@pytest.fixture
def tracker(tmp_path):
    return ExperimentTracker(tmp_path / "experiments")


def test_start_and_finish(tracker):
    s = tracker.start_run("run-1", "job-1", {"base_model_id": "m", "output_model_id": "m2"})
    assert s.status == "running"
    tracker.finish_run("run-1", "completed")
    s2 = tracker.get_run("run-1")
    assert s2.status == "completed"
    assert s2.finished_at is not None


def test_log_metrics(tracker):
    tracker.start_run("run-2", "job-2", {})
    tracker.log_metric("run-2", MetricPoint(step=1, epoch=0, loss=2.5, lr=1e-4, elapsed_s=1.0))
    tracker.log_metric("run-2", MetricPoint(step=2, epoch=0, loss=2.1, lr=1e-4, elapsed_s=2.0))
    metrics = tracker.get_metrics("run-2")
    assert len(metrics) == 2
    assert metrics[-1].loss == 2.1


def test_best_loss_tracked(tracker):
    tracker.start_run("run-3", "job-3", {})
    tracker.log_metric("run-3", MetricPoint(step=1, epoch=0, loss=3.0, lr=1e-4, elapsed_s=1.0))
    tracker.log_metric("run-3", MetricPoint(step=2, epoch=0, loss=1.5, lr=1e-4, elapsed_s=2.0))
    s = tracker.get_run("run-3")
    assert s.best_loss == 1.5


def test_list_runs(tracker):
    tracker.start_run("r1", "j1", {})
    tracker.start_run("r2", "j2", {})
    runs = tracker.list_runs()
    ids = [r.run_id for r in runs]
    assert "r1" in ids and "r2" in ids
