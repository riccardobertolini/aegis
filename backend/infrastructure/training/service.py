"""TrainingService — implements ITrainingPort, orchestrates all training components."""
from __future__ import annotations

import asyncio
import logging
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from backend.domain.ports.training import (
    CheckpointInfo,
    ExperimentMetrics,
    ITrainingPort,
    JobStatus,
    TrainingConfig,
    TrainingJob,
)
from backend.infrastructure.training.checkpoint_manager import CheckpointManager
from backend.infrastructure.training.dataset import DatasetManager
from backend.infrastructure.training.experiment_tracker import ExperimentTracker
from backend.infrastructure.training.trainer import MambaTrainer

logger = logging.getLogger(__name__)


class TrainingService(ITrainingPort):
    """
    Orchestrates dataset loading, training loop, experiment tracking,
    checkpointing and model promotion.

    Training runs in a background ThreadPoolExecutor (non-blocking async API).
    """

    def __init__(
        self,
        models_root: Path,
        experiments_root: Path,
        datasets_root: Path,
        model_loader,   # MambaModelLoader from inference
        max_concurrent_jobs: int = 1,
    ) -> None:
        self._models_root = models_root
        self._dataset_mgr = DatasetManager(datasets_root)
        self._tracker = ExperimentTracker(experiments_root)
        self._ckpt_mgr = CheckpointManager(experiments_root)
        self._loader = model_loader
        self._executor = ThreadPoolExecutor(max_workers=max_concurrent_jobs)
        self._jobs: dict[str, TrainingJob] = {}
        self._cancel_events: dict[str, threading.Event] = {}

    # ------------------------------------------------------------------
    # ITrainingPort
    # ------------------------------------------------------------------

    async def start_job(self, config: TrainingConfig) -> TrainingJob:
        if not config.job_id:
            config.job_id = str(uuid.uuid4())

        job = TrainingJob(
            config=config,
            status=JobStatus.PENDING,
            started_at=datetime.now(timezone.utc),
        )
        self._jobs[config.job_id] = job
        cancel_ev = threading.Event()
        self._cancel_events[config.job_id] = cancel_ev

        loop = asyncio.get_event_loop()
        loop.run_in_executor(
            self._executor,
            self._run_job_sync,
            config.job_id,
            cancel_ev,
        )
        logger.info("Training job %s queued", config.job_id)
        return job

    async def get_job(self, job_id: str) -> TrainingJob:
        job = self._jobs.get(job_id)
        if job is None:
            raise KeyError(f"Job '{job_id}' not found")
        return job

    async def cancel_job(self, job_id: str) -> None:
        ev = self._cancel_events.get(job_id)
        if ev:
            ev.set()
        job = self._jobs.get(job_id)
        if job and job.status == JobStatus.RUNNING:
            job.status = JobStatus.CANCELLED
            logger.info("Job %s cancel requested", job_id)

    async def list_jobs(self) -> list[TrainingJob]:
        return list(self._jobs.values())

    async def get_metrics(self, job_id: str) -> list[ExperimentMetrics]:
        return self._tracker.read_metrics(job_id)

    async def list_checkpoints(self, job_id: str) -> list[CheckpointInfo]:
        return self._ckpt_mgr.list_checkpoints(job_id)

    async def promote_checkpoint(
        self, job_id: str, step: int, target_model_id: str
    ) -> str:
        sha256 = self._ckpt_mgr.promote(
            job_id, step, self._models_root, target_model_id
        )
        # Rescan inference loader so the new model is immediately available
        try:
            self._loader.scan()
        except Exception as exc:
            logger.warning("Loader rescan after promotion failed: %s", exc)
        return sha256

    # ------------------------------------------------------------------
    # Background execution
    # ------------------------------------------------------------------

    def _run_job_sync(self, job_id: str, cancel_ev: threading.Event) -> None:
        job = self._jobs[job_id]
        job.status = JobStatus.RUNNING
        try:
            self._execute_training(job, cancel_ev)
        except Exception as exc:
            logger.exception("Training job %s failed: %s", job_id, exc)
            job.status = JobStatus.FAILED
            job.error = str(exc)
            job.finished_at = datetime.now(timezone.utc)

    def _execute_training(self, job: TrainingJob, cancel_ev: threading.Event) -> None:
        cfg = job.config

        # Load base model
        try:
            self._loader.scan()
            model = self._loader.load(cfg.base_model_id)
            tokenizer = self._loader.get_tokenizer(cfg.base_model_id)
        except Exception as exc:
            raise RuntimeError(f"Cannot load base model '{cfg.base_model_id}': {exc}") from exc

        # Load dataset
        texts = self._dataset_mgr.load_texts(cfg.dataset_path)
        if not texts:
            raise ValueError(f"Dataset at '{cfg.dataset_path}' is empty.")

        split = self._dataset_mgr.split(texts, seed=cfg.seed)
        logger.info(
            "Dataset: %d train / %d val / %d test samples",
            len(split.train), len(split.val), len(split.test),
        )

        # Init experiment tracking
        import dataclasses
        self._tracker.init_experiment(cfg.job_id, dataclasses.asdict(cfg))

        def on_progress(frac: float, step: int, epoch: int) -> None:
            job.progress = round(frac, 4)
            job.current_step = step
            job.current_epoch = epoch

        trainer = MambaTrainer(
            config=cfg,
            model=model,
            tokenizer=tokenizer,
            tracker=self._tracker,
            ckpt_manager=self._ckpt_mgr,
            cancel_event=cancel_ev,
            on_progress=on_progress,
        )

        summary = trainer.run(split.train, split.val)

        job.status = (
            JobStatus.CANCELLED if cancel_ev.is_set() else JobStatus.COMPLETED
        )
        job.best_val_loss = summary.get("best_val_loss")
        job.checkpoints = self._ckpt_mgr.list_checkpoints(cfg.job_id)
        job.finished_at = datetime.now(timezone.utc)
        job.progress = 1.0

        logger.info(
            "Job %s %s — best_val_loss=%s",
            cfg.job_id, job.status, job.best_val_loss,
        )
