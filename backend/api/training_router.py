"""Training Engine REST API."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/training", tags=["training"])


def _svc(request: Request):
    c = getattr(request.app.state, "training_container", None)
    if c is None:
        raise HTTPException(status_code=503, detail="TrainingService not initialised")
    return c.service


class JobRequest(BaseModel):
    base_model_id: str
    dataset_path: str
    output_model_id: str
    epochs: int = Field(3, ge=1, le=100)
    learning_rate: float = Field(1e-4, gt=0)
    batch_size: int = Field(8, ge=1, le=256)
    max_seq_len: int = Field(512, ge=32, le=8192)
    grad_clip: float = Field(1.0, gt=0)
    warmup_steps: int = Field(0, ge=0)
    save_every_n_steps: int = Field(100, ge=1)
    eval_every_n_steps: int = Field(50, ge=1)
    seed: int = 42


class JobOut(BaseModel):
    job_id: str
    status: str
    progress: float
    current_step: int
    current_epoch: int
    best_val_loss: float | None
    error: str | None
    started_at: str | None
    finished_at: str | None


class PromoteRequest(BaseModel):
    step: int
    target_model_id: str


def _job_out(job) -> JobOut:
    return JobOut(
        job_id=job.config.job_id,
        status=job.status.value,
        progress=job.progress,
        current_step=job.current_step,
        current_epoch=job.current_epoch,
        best_val_loss=job.best_val_loss,
        error=job.error,
        started_at=job.started_at.isoformat() if job.started_at else None,
        finished_at=job.finished_at.isoformat() if job.finished_at else None,
    )


@router.post("/jobs", response_model=JobOut, status_code=202)
async def start_job(body: JobRequest, request: Request):
    from backend.domain.ports.training import TrainingConfig
    import uuid
    cfg = TrainingConfig(
        job_id=str(uuid.uuid4()),
        base_model_id=body.base_model_id,
        dataset_path=body.dataset_path,
        output_model_id=body.output_model_id,
        epochs=body.epochs,
        learning_rate=body.learning_rate,
        batch_size=body.batch_size,
        max_seq_len=body.max_seq_len,
        grad_clip=body.grad_clip,
        warmup_steps=body.warmup_steps,
        save_every_n_steps=body.save_every_n_steps,
        eval_every_n_steps=body.eval_every_n_steps,
        seed=body.seed,
    )
    job = await _svc(request).start_job(cfg)
    return _job_out(job)


@router.get("/jobs", response_model=list[JobOut])
async def list_jobs(request: Request):
    jobs = await _svc(request).list_jobs()
    return [_job_out(j) for j in jobs]


@router.get("/jobs/{job_id}", response_model=JobOut)
async def get_job(job_id: str, request: Request):
    try:
        job = await _svc(request).get_job(job_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Job not found")
    return _job_out(job)


@router.delete("/jobs/{job_id}", status_code=204)
async def cancel_job(job_id: str, request: Request):
    await _svc(request).cancel_job(job_id)


@router.get("/jobs/{job_id}/metrics")
async def get_metrics(job_id: str, request: Request):
    metrics = await _svc(request).get_metrics(job_id)
    return [
        {
            "step": m.step, "epoch": m.epoch,
            "train_loss": m.train_loss, "val_loss": m.val_loss,
            "lr": m.learning_rate, "tok_per_sec": m.tokens_per_second,
            "ts": m.timestamp.isoformat(),
        }
        for m in metrics
    ]


@router.get("/jobs/{job_id}/checkpoints")
async def list_checkpoints(job_id: str, request: Request):
    ckpts = await _svc(request).list_checkpoints(job_id)
    return [
        {
            "step": c.step, "epoch": c.epoch,
            "train_loss": c.train_loss, "val_loss": c.val_loss,
            "path": c.path,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in ckpts
    ]


@router.post("/jobs/{job_id}/promote")
async def promote(job_id: str, body: PromoteRequest, request: Request):
    sha256 = await _svc(request).promote_checkpoint(
        job_id, body.step, body.target_model_id
    )
    return {"target_model_id": body.target_model_id, "sha256": sha256}


@router.get("/datasets")
async def list_datasets(request: Request):
    c = getattr(request.app.state, "training_container", None)
    if c is None:
        raise HTTPException(status_code=503, detail="TrainingService not initialised")
    infos = c.service._dataset_mgr.list_datasets()
    return [
        {
            "name": d.name, "format": d.format, "split": d.split,
            "num_samples": d.num_samples, "sha256": d.sha256,
            "path": str(d.path),
        }
        for d in infos
    ]
