"""DI factory for Training Engine."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from backend.infrastructure.training.service import TrainingService


@dataclass
class TrainingContainer:
    service: TrainingService


def build_training_container(
    models_root: Path,
    experiments_root: Path,
    datasets_root: Path,
    model_loader,
    max_concurrent_jobs: int = 1,
) -> TrainingContainer:
    svc = TrainingService(
        models_root=models_root,
        experiments_root=experiments_root,
        datasets_root=datasets_root,
        model_loader=model_loader,
        max_concurrent_jobs=max_concurrent_jobs,
    )
    return TrainingContainer(service=svc)
