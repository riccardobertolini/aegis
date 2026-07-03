"""Training Engine REST API.

All endpoints are offline-only, no telemetry.

Endpoints
---------
POST   /training/jobs                  — start a fine-tuning job
GET    /training/jobs                  — list all jobs
GET    /training/jobs/{job_id}          — get single job
DELETE /training/jobs/{job_id}          — cancel job
GET    /training/datasets               — list ingested datasets
POST   /training/datasets               — ingest a local dataset file
GET    /training/experiments            — list experiment runs
GET    /training/experiments/{run_id}/metrics  — metrics JSONL
GET    /training/checkpoints/{run_id}   — list checkpoints
POST   /training/models/{model_id}/sign     — sign model
GET    /training/models/{model_id}/verify   — verify model integrity
POST   /training/models/{model_id}/evaluate — compute perplexity on eval set
"""
from __future__ import annotations

import uuid
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.domain.ports.training import TrainingConfig, TrainingJob

router = APIRouter(prefix="/training", tags=["Training"])


# ------------------------------------------------------------------
# Pydantic schemas
# ------------------------------------------------------------------

class StartJobRequest(BaseModel):
    base_model_id: str
    dataset_name: str = Field(..., description="Name of an already-ingested dataset")
    output_model_id: str
    epochs: int = 3
    learning_rate: float = 1e-4
    batch_size: int = 4
    max_length: int = 512
    text_field: str = "text"


class JobResponse(BaseModel):
    job_id: str
    status: str
    progress: float
    logs: list[str]


class IngestRequest(BaseModel):
    name: str
    source_path: str = Field(..., description="Absolute or relative path to the source file on this machine")
    split: str = "train"
    text_field: str = "text"


class EvaluateRequest(BaseModel):
    dataset_name: str
    max_chunks: int = 64


# ------------------------------------------------------------------
# Dependency
# ------------------------------------------------------------------

def _get_svc():
    """Resolved at startup by main.py via app.state."""
    from backend.main import app  # lazy import to avoid circular
    svc = getattr(app.state, "training_service", None)
    if svc is None:
        raise HTTPException(status_code=503, detail="Training engine not initialised")
    return svc


TrainingSvc = Annotated[object, Depends(_get_svc)]


# ------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------

@router.post("/jobs", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_job(req: StartJobRequest, svc: TrainingSvc):
    job_id = f"job-{uuid.uuid4().hex[:12]}"
    config = TrainingConfig(
        job_id=job_id,
        base_model_id=req.base_model_id,
        dataset_path=req.dataset_name,
        output_model_id=req.output_model_id,
        epochs=req.epochs,
        learning_rate=req.learning_rate,
        batch_size=req.batch_size,
        extra={"max_length": req.max_length, "text_field": req.text_field},
    )
    job = await svc.start_job(config)
    return _job_resp(job)


@router.get("/jobs", response_model=list[JobResponse])
async def list_jobs(svc: TrainingSvc):
    jobs = await svc.list_jobs()
    return [_job_resp(j) for j in jobs]


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str, svc: TrainingSvc):
    try:
        job = await svc.get_job(job_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    return _job_resp(job)


@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_job(job_id: str, svc: TrainingSvc):
    await svc.cancel_job(job_id)


@router.get("/datasets")
def list_datasets(svc: TrainingSvc):
    return {"datasets": svc.list_datasets()}


@router.post("/datasets", status_code=status.HTTP_201_CREATED)
def ingest_dataset(req: IngestRequest, svc: TrainingSvc):
    src = Path(req.source_path)
    if not src.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {req.source_path}")
    version = svc._datasets.ingest(req.name, src, split=req.split)
    return version.to_dict()


@router.get("/experiments")
def list_experiments(svc: TrainingSvc):
    runs = svc.list_experiments()
    return {"runs": [r.to_dict() for r in runs]}


@router.get("/experiments/{run_id}/metrics")
def get_metrics(run_id: str, svc: TrainingSvc):
    from dataclasses import asdict
    metrics = svc.get_experiment_metrics(run_id)
    return {"run_id": run_id, "metrics": [asdict(m) for m in metrics]}


@router.get("/checkpoints/{run_id}")
def list_checkpoints(run_id: str, svc: TrainingSvc):
    from dataclasses import asdict
    ckpts = svc.list_checkpoints(run_id)
    return {"run_id": run_id, "checkpoints": [asdict(c) for c in ckpts]}


@router.post("/models/{model_id}/sign")
def sign_model(model_id: str, svc: TrainingSvc):
    try:
        manifest = svc.sign_model(model_id)
        return {"model_id": model_id, "signed": True, "files": len(manifest.get("files", {}))}
    except NotADirectoryError:
        raise HTTPException(status_code=404, detail=f"Model '{model_id}' not found")


@router.get("/models/{model_id}/verify")
def verify_model(model_id: str, svc: TrainingSvc):
    ok = svc.verify_model(model_id)
    return {"model_id": model_id, "integrity_ok": ok}


@router.post("/models/{model_id}/evaluate")
def evaluate_model(model_id: str, req: EvaluateRequest, svc: TrainingSvc):
    try:
        result = svc.evaluate_model(model_id, req.dataset_name, req.max_chunks)
        return {"model_id": model_id, **result}
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc))


# ------------------------------------------------------------------
# Helper
# ------------------------------------------------------------------

def _job_resp(job: TrainingJob) -> dict:
    return {
        "job_id": job.config.job_id,
        "status": job.status.value,
        "progress": job.progress,
        "logs": job.logs,
    }
