# Phase 8 — Training Engine + Fine-Tuning (Local, Offline)

## Overview

The Training Engine provides a complete local pipeline for fine-tuning Mamba/SSM models without any cloud dependency, telemetry, or automatic weight download.

```
datasets/          ← Drop .jsonl or .txt files here
experiments/       ← Auto-created: one dir per job
  <job_id>/
    config.json    ← TrainingConfig snapshot
    metrics.jsonl  ← Append-only step metrics
    summary.json   ← Final run summary
    checkpoints/
      step_00000100/
        model.pt
        meta.json  ← CheckpointInfo + SHA-256
models/            ← Promoted models land here (picked up by InferenceEngine)
```

## Components

| Module | Responsibility |
|---|---|
| `dataset.py` | Load JSONL/TXT, split train/val/test, SHA-256 versioning |
| `preprocessor.py` | Tokenise texts, sliding-window chunking, batch iterator |
| `experiment_tracker.py` | Append-only JSONL metrics, config snapshot, summary |
| `checkpoint_manager.py` | Save/load/verify checkpoints, promote to `models/` |
| `trainer.py` | PyTorch training loop (AdamW, LR warmup, grad clip, eval) |
| `service.py` | ITrainingPort impl, background ThreadPoolExecutor, DI |
| `container.py` | DI factory |

## REST API (`/api/v1/training`)

| Method | Path | Description |
|---|---|---|
| `POST` | `/jobs` | Start a fine-tuning job (async, returns immediately) |
| `GET` | `/jobs` | List all jobs |
| `GET` | `/jobs/{id}` | Get job status + progress |
| `DELETE` | `/jobs/{id}` | Cancel a running job |
| `GET` | `/jobs/{id}/metrics` | Step-level metrics (loss, LR, tok/s) |
| `GET` | `/jobs/{id}/checkpoints` | List saved checkpoints |
| `POST` | `/jobs/{id}/promote` | Copy checkpoint to `models/` and register |
| `GET` | `/datasets` | List discovered datasets |

## Dataset Format

**JSONL** (recommended):
```jsonl
{"text": "Sample sentence for training."}
{"text": "Another example with domain-specific content."}
```

**TXT**: one sample per non-empty line.

Place files under `datasets/`. Subdirectories are scanned recursively.

## Launching a Fine-Tuning Job

```bash
# 1. Place dataset
cp my_corpus.jsonl datasets/my_corpus.jsonl

# 2. Start job via API
curl -X POST http://localhost:8000/api/v1/training/jobs \
  -H 'Content-Type: application/json' \
  -d '{
    "base_model_id": "mamba-130m",
    "dataset_path": "datasets/my_corpus.jsonl",
    "output_model_id": "mamba-130m-finetuned",
    "epochs": 3,
    "learning_rate": 1e-4,
    "batch_size": 4,
    "max_seq_len": 512
  }'

# 3. Poll status
curl http://localhost:8000/api/v1/training/jobs/<job_id>

# 4. Promote best checkpoint
curl -X POST http://localhost:8000/api/v1/training/jobs/<job_id>/promote \
  -H 'Content-Type: application/json' \
  -d '{"step": 300, "target_model_id": "mamba-130m-v2"}'

# 5. Inference with promoted model (picked up on next server restart or dynamic scan)
curl -X POST http://localhost:8000/api/v1/inference/completions \
  -d '{"model_id": "mamba-130m-v2", "prompt": "Aegis is", "max_tokens": 64}'
```

## Hardware Notes

- **CPU**: supported via `mamba-minimal`. Training is slow but functional for small models and datasets.
- **GPU (CUDA)**: `mamba-ssm` provides full CUDA-accelerated training. Recommended for models ≥ 370M params or datasets ≥ 10k samples.
- `max_concurrent_jobs=1` by default — prevent OOM on single-GPU machines.

## Offline Compliance

- No MLflow, W&B, Neptune, or any remote tracking service.
- All metrics written to local `experiments/<job_id>/metrics.jsonl`.
- All weights stay in `experiments/` until explicitly promoted to `models/`.
- SHA-256 on every checkpoint; verified on load.
- Dataset SHA-256 sidecar files detect accidental data drift.
