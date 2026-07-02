# Aegis — Inference Engine (Phase 1)

## Rationale: Why Mamba / SSM?

| Property | Transformer | Mamba SSM |
|---|---|---|
| Sequence complexity | O(n²) attention | O(n) linear recurrence |
| Memory (long ctx) | Grows quadratically | Constant (state size) |
| Hardware req. | Large GPU cluster | Single GPU or CPU |
| Cloud dependency | Often required | **Zero — fully local** |
| Air-gapped? | Hard without ONNX | **Native support** |

Mamba's selective state-space mechanism achieves quality comparable to Transformers of the same parameter count, at a fraction of the memory and compute cost — making it the only viable choice for an air-gapped, single-machine enterprise platform.

## Architecture

```
models/                          ← drop model dirs here manually
  my-mamba-chat/
    config.json                  ← required: d_model, n_layer, vocab_size
    model.safetensors            ← weights (.pt or .safetensors)
    tokenizer.json               ← optional (ByteLevel fallback if absent)

backend/infrastructure/inference/
  loader.py      MambaModelLoader  — scans, parses config, loads weights
  adapter.py     MambaInferenceAdapter  — IInferencePort impl
  core_ai.py     CoreAIService         — ICoreAIPort impl (full pipeline)
  container.py   InferenceContainer    — DI factory

backend/api/
  inference_router.py  — REST endpoints
```

## Component Responsibilities

### `MambaModelLoader`
- Scans `models/` at startup; no network call ever happens
- Tries `mamba-ssm` (CUDA) first, falls back to `mamba-minimal` (CPU)
- Caches model objects in memory; `unload()` frees GPU memory via `torch.cuda.empty_cache()`
- Tokenizer hierarchy: `tokenizer.json` → `vocab.json` → `_ByteLevelFallbackTokenizer`

### `MambaInferenceAdapter`
- Runs all blocking inference in a thread-pool executor (never blocks the async event loop)
- Supports greedy decoding, temperature sampling, top-p nucleus sampling, repetition penalty
- Streaming: yields tokens via `asyncio.Queue` bridging the thread-pool to the async generator

### `CoreAIService`
- Pipeline: Intent (optional) → Memory recall (optional) → Inference → Memory store (optional)
- Prompt format (ChatML-style):
  ```
  <|system|>\n{system_prompt}\n
  <|user|>\n{user_turn}\n
  <|assistant|>\n{assistant_turn}\n
  ...
  <|user|>\n{current_input}\n
  <|assistant|>\n          ← model generates from here
  ```
- All engine failures (intent, memory) are caught and logged — pipeline never crashes

## Dropping in a Model

1. Copy model directory to `models/<your-model-name>/`
2. Ensure `config.json` contains at minimum:
   ```json
   { "model_type": "mamba", "d_model": 768, "n_layer": 24, "vocab_size": 50280 }
   ```
3. Place weights as `model.safetensors` or `model.pt`
4. (Optional) add `tokenizer.json` for proper tokenization
5. Restart Aegis — the model appears in `GET /api/v1/inference/models`
6. Load it: `POST /api/v1/inference/models/<your-model-name>/load`

**No download, no internet, no cloud.** The server never calls out.

## CPU vs GPU

| Mode | Backend | Requirement |
|---|---|---|
| GPU | `mamba-ssm` | CUDA + `requirements/ml.txt` GPU section |
| CPU | `mamba-minimal` | Pure Python/PyTorch CPU |

The loader tries GPU first and falls back automatically.

## API Reference

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/inference/models` | List all local models |
| `GET` | `/api/v1/inference/models/{id}` | Model details |
| `POST` | `/api/v1/inference/models/{id}/load` | Load model into memory |
| `DELETE` | `/api/v1/inference/models/{id}` | Unload model |
| `POST` | `/api/v1/inference/completions` | Single completion |
| `POST` | `/api/v1/inference/completions/stream` | SSE token streaming |
| `POST` | `/api/v1/ai/chat` | Full CoreAI pipeline |

## Integrity Integration (Phase 6)

Before loading a model, `ModelIntegrityService.verify(model_id)` can be called
to check the SHA-256 against the stored hash in the DB. If the hash has never
been registered, `register(model_id)` seeds it on first load.
This is wired optionally via `InferenceContainer.build(integrity=...)` (future hook).

## Configuration (.env / Settings)

```env
DEFAULT_MODEL_ID=my-mamba-chat
SYSTEM_PROMPT="You are Aegis, a helpful AI assistant running fully offline."
MODELS_ROOT=./models
```
