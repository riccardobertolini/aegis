# Inference Module — Documentation

## Overview

The Inference Module implements FASE 1 of Aegis: **local Mamba/SSM-based text generation**.
No network calls occur anywhere in this module. All weights are loaded from `AEGIS_MODELS_DIR`.

## Architecture

```
FastAPI Router (api/v1/inference.py)
        │
        ▼
 CoreAIService (application/inference/core_ai_service.py)
        │
        ▼
 InferenceEngine (application/inference/inference_engine.py)
   ├── ModelRegistry  ── scans models/ dir, validates metadata
   ├── ModelSigner    ── SHA-256 + HMAC-SHA256 integrity
   ├── ContextManager ── rolling window, compression, incremental summary
   └── IModelProvider ── interface to the actual SSM backend
           │
           ├── MambaModelProvider  (GPU: mamba-ssm)
           ├── MambaModelProvider  (CPU: mamba-minimal fallback)
           └── StubModel           (tests, no weights needed)
```

## Model Storage Layout

```
models/
└── <model_id>/
    ├── metadata.json      ← registered with ModelRegistry
    ├── model.pt           ← PyTorch checkpoint (Mamba state dict)
    ├── config.json        ← Mamba architecture config
    └── tokenizer.json     ← tokenizer vocab + merges
```

### metadata.json schema

```json
{
  "model_id":          "mamba-130m-v1",
  "architecture":      "mamba",
  "version":           "1.0.0",
  "description":       "Mamba 130M base model, offline fine-tuned",
  "language":          "it",
  "context_length":    2048,
  "hidden_dim":        768,
  "num_layers":        24,
  "vocab_size":        50257,
  "quantization":      "none",
  "checkpoint_file":   "model.pt",
  "config_file":       "config.json",
  "tokenizer_file":    "tokenizer.json",
  "sha256_checkpoint": "<64-char hex>",
  "sha256_tokenizer":  "<64-char hex>",
  "signature":         "<HMAC-SHA256 of this dict>",
  "created_at":        "2026-07-02T10:00:00",
  "tags":              ["base", "italian"]
}
```

## Security: Model Integrity

Every model is verified before loading:
1. `ModelSigner.verify_file(checkpoint_path, sha256_checkpoint)` — SHA-256 of weights
2. `ModelSigner.verify_file(tokenizer_path, sha256_tokenizer)` — SHA-256 of tokenizer
3. `ModelSigner.verify_metadata(metadata_dict)` — HMAC-SHA256 of all metadata fields

If any check fails, `ModelLoadError` is raised and the model is **not loaded**.

To register a new model:
```bash
python -m backend.cli.register_model --model-dir models/mamba-130m-v1/ --secret-key-file secrets/signing.key
```
(CLI implemented in later phase)

## RuntimeConfig

| Parameter | Default | Description |
|---|---|---|
| `device` | `auto` | `cpu` \| `cuda` \| `mps` \| `auto` |
| `quantization` | `none` | `none` \| `int8` \| `int4` \| `fp16` \| `bf16` |
| `max_context_length` | 2048 | Rolling window size in tokens |
| `max_new_tokens` | 512 | Max generated tokens per request |
| `temperature` | 0.7 | Sampling temperature |
| `top_p` | 0.9 | Nucleus sampling probability |
| `top_k` | 50 | Top-K sampling |
| `repetition_penalty` | 1.1 | Penalise repeated tokens |
| `use_kv_cache` | true | Enable Mamba hidden-state cache |
| `enable_context_compression` | true | Auto-compress over-length contexts |
| `compression_ratio` | 0.5 | Fraction of middle tokens to keep |
| `incremental_summary_every_n` | 256 | Tokens between summary updates |
| `stream_chunk_size` | 1 | Tokens per SSE chunk |

## Context Compression

When `effective_length > max_context_length`:
1. Head (5%) and tail (30%) are always preserved.
2. Middle tokens are scored by inverse frequency (rare = high importance).
3. Bottom `1 - compression_ratio` fraction is dropped.
4. Dropped tokens become a stub `summary_prefix` (full summarisation via Inference in later phase).

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/inference/models` | List available models |
| `POST` | `/api/v1/inference/generate` | Generate text (sync or SSE stream) |
| `POST` | `/api/v1/inference/models/{id}/load` | Pre-load model into memory |
| `DELETE` | `/api/v1/inference/models/{id}/unload` | Release model from memory |

## Running Tests

```bash
# All inference unit tests
pytest tests/unit/test_stub_backend.py tests/unit/test_model_signer.py \
       tests/unit/test_model_metadata.py tests/unit/test_context_manager.py \
       tests/unit/test_runtime_config.py tests/unit/test_inference_engine.py \
       tests/unit/test_core_ai_service.py -v

# Benchmark
pytest tests/unit/test_benchmark_latency.py -v -s
```

No model weights are required for any of the above tests.
