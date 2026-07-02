# Aegis

> **Enterprise AI platform — Offline-First, Air-Gapped, Mamba/SSM only.**

## Overview

Aegis is a fully local, air-gapped AI platform built on State Space Models (Mamba/SSM).  
No cloud, no external APIs, no telemetry — ever.

## Components

| Component | Description |
|---|---|
| **admin-studio** | Full administration UI (React) |
| **client** | Minimal end-user interface (React) |
| **backend** | Python core — all engines, inference, storage |
| **packaging** | Offline installer, wheelhouse builder |
| **docs** | Architecture, API reference, runbooks |

## Architecture

See [`docs/architecture/overview.md`](docs/architecture/overview.md).

## Quick Start (offline)

```bash
# 1. Build wheelhouse on a connected machine
pip download -r requirements/base.txt -d wheelhouse/

# 2. Install from wheelhouse on air-gapped machine
pip install --no-index --find-links=wheelhouse/ -r requirements/base.txt

# 3. Start backend
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

## Stack

- **Inference**: Mamba (SSM) via `mamba-ssm` or `causal-conv1d` — no Transformers as primary engine
- **Vector store**: ChromaDB (local, embedded)
- **DB**: SQLite (via SQLModel) + DuckDB for analytics
- **Backend**: FastAPI + Python 3.11+
- **Frontend**: React 18 + Vite
- **Testing**: Pytest + Vitest

## Constraints (inviolable)

- ❌ No internet calls (HTTP/WS/gRPC to external hosts)
- ❌ No automatic model downloads
- ❌ No telemetry or analytics
- ❌ No Transformer as primary inference engine
- ✅ All data stays on the machine
- ✅ Operable in fully isolated networks

## License

MIT — see [LICENSE](LICENSE).
