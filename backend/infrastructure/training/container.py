"""DI factory for the Training Engine."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.infrastructure.training.dataset import DatasetManager
from backend.infrastructure.training.experiment import ExperimentTracker
from backend.infrastructure.training.checkpoint import CheckpointManager
from backend.infrastructure.training.signer import ModelSigner
from backend.infrastructure.training.service import TrainingService


def build_training_container(
    model_loader: Any,
    models_root: Path | str = "models",
    datasets_root: Path | str = "datasets",
    experiments_root: Path | str = "experiments",
    checkpoints_root: Path | str = "checkpoints",
    hmac_secret: bytes = b"aegis-training-secret",
) -> TrainingService:
    """Wire all training components and return a ready TrainingService.

    Parameters
    ----------
    model_loader:
        ``MambaModelLoader`` instance from the Inference container.
    models_root, datasets_root, experiments_root, checkpoints_root:
        Filesystem roots for each artifact type.  Accepts str or Path.
    hmac_secret:
        Secret for model signing; override in production via settings.
    """
    models_root = Path(models_root)
    datasets_root = Path(datasets_root)
    experiments_root = Path(experiments_root)
    checkpoints_root = Path(checkpoints_root)

    dataset_manager = DatasetManager(datasets_root)
    tracker = ExperimentTracker(experiments_root)
    checkpoint_manager = CheckpointManager(checkpoints_root)
    signer = ModelSigner(hmac_secret=hmac_secret)

    return TrainingService(
        model_loader=model_loader,
        dataset_manager=dataset_manager,
        tracker=tracker,
        checkpoint_manager=checkpoint_manager,
        signer=signer,
        models_root=models_root,
    )
