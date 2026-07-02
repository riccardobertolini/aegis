# Phase 5 — Memory, LogEngine, TimeSeries, Translation

## Memory Engine

Short-term and long-term conversation memory stored in **SQLite** via SQLModel/aiosqlite. Two tables:

| Table | Content |
|---|---|
| `conversation_turns` | Every user/assistant/system message, with session_id, role, intent, metadata |
| `session_summaries` | One row per session: extractive or SSM-generated summary + turn count |

### Summarisation strategy

- **Default (no inference)**: extractive — first user message + last assistant message + turn count.
- **With inference**: if `IInferencePort` is injected, sends a compact prompt to the local Mamba engine. Falls back to extractive if the model fails.

### REST API (`/api/v1/memory`)

| Method | Path | Description |
|---|---|---|
| `POST` | `/turns` | Append a turn |
| `GET` | `/sessions/{id}/history` | Last N turns |
| `DELETE` | `/sessions/{id}` | Clear session |
| `POST` | `/sessions/{id}/summarize` | Generate + store summary |
| `GET` | `/sessions/{id}/summary` | Retrieve stored summary |
| `GET` | `/sessions` | List session IDs (paginated) |

---

## Log Engine

Append-only structured log store using **DuckDB** (embedded, local `.duckdb` file). Provides fast columnar queries by `level`, `component`, `session_id`, `timestamp` range.

- Sync API (non-blocking for append-only; wrap with `run_in_executor` if needed inside async context).
- Thread-safe via a per-instance `threading.Lock()`.
- Complement to the structlog rotating file sink (Fase 0): this is the queryable analytics layer.

---

## TimeSeries Engine

Numeric metric store (latency, token counts, errors, usage) in **DuckDB**. Supports:

- `record(name, value, tags, unit)` — ingest a metric point.
- `query(name, since, until)` — raw rows.
- `aggregate(name, agg, bucket)` — time-bucketed `avg/sum/min/max/count`.

---

## Translation Engine

Fully offline translation via **Argos Translate** (local language packages). Language packages must be installed offline before first use:

```bash
# Install argostranslate
pip install argostranslate

# Download and install a package offline (on an internet-connected machine)
python -c "
import argostranslate.package as p
p.update_package_index()
available = p.get_available_packages()
pkg = next(a for a in available if a.from_code=='it' and a.to_code=='en')
pkg.install()
"
# Then copy ~/.local/share/argos-translate/ to the air-gapped machine
```

If argostranslate is not installed, the service returns the source text unchanged with a warning — the platform continues to function.

---

## Air-gap compliance

- SQLite: local `.db` file, no server.
- DuckDB: local `.duckdb` file, no server.
- Argos Translate: `local_packages_dir` points to a copied directory; no HTTP calls.
- Memory summarisation via Mamba SSM: reuses the already-local inference engine.
