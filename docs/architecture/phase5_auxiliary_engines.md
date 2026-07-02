# FASE 5 — Auxiliary Engines

## Overview

Questa fase implementa i quattro engine ausiliari che completano la piattaforma AEGIS:

| Engine | Port | Storage | Dipendenze chiave |
|---|---|---|---|
| Memory | `IMemoryPort` | SQLite (`aiosqlite`) | nessuna ML |
| Translation | `ITranslationPort` | file-system (modelli) | `langdetect`, `ctranslate2` (opzionale) |
| TimeSeries | `ITimeSeriesPort` | DuckDB | `duckdb` |
| Log | `ILogEnginePort` | DuckDB | `duckdb` |

---

## Memory Engine

### Architettura

```
MemoryEngine
├── append()            → INSERT INTO memory_entries
├── get_history()       → SELECT + windowing logico
├── clear_session()     → DELETE + DELETE summaries
├── summarize_session() → extractive (default) / abstractive (+ CoreAI)
└── list_sessions()     → DISTINCT session_id
```

### Long-context windowing

Se una sessione supera `_WINDOW_SIZE = 40` entry:
1. Viene generato (o recuperato) un **rolling summary** dalla tabella `memory_summaries`.
2. Il summary viene anteposto come entry sintetica di ruolo `system`.
3. Solo le ultime `min(last_n, 40)` entry vengono restituite.

Questo consente contesti lunghi senza passare token illimitati al motore SSM.

### Summarisation strategy

| Modalità | Quando | Algoritmo |
|---|---|---|
| Extractive | `core_ai is None` | TF-IDF word frequency (Luhn semplificato) |
| Abstractive | `core_ai` iniettato | Prompt al CoreAI (FASE 6+) |

### Namespace per assistente

Il campo `metadata.assistant_id` nel `MemoryEntry` consente di filtrare sessioni per assistente tramite `list_sessions(assistant_id=...)`.

---

## Translation Engine

### Architettura

```
TranslationEngine
├── translate()             → detect_lang → dispatch model → result
├── list_language_pairs()   → lista statica delle 12 coppie
└── _run_model()            → ctranslate2 (se modello presente) | rule-based
```

### Strategia layered

```
[1] CTranslate2 + Helsinki-NLP OPUS-MT (modello locale in models/translation/)
    ↓ (se assente)
[2] Pivot via English (es. IT→DE = IT→EN + EN→DE)
    ↓ (se coppia non supportata o modello mancante)
[3] Rule-based word substitution (smoke-test / air-gap senza modelli)
```

### Installazione modelli (air-gap)

```bash
# Scarica una volta su macchina connessa:
pip download ctranslate2 sentencepiece langdetect -d wheelhouse/
# Scarica modelli Helsinki-NLP:
python -c "
from transformers import MarianMTModel, MarianTokenizer
MarianMTModel.from_pretrained('Helsinki-NLP/opus-mt-it-en').save_pretrained('models/translation/opus-mt-it-en')
MarianTokenizer.from_pretrained('Helsinki-NLP/opus-mt-it-en').save_pretrained('models/translation/opus-mt-it-en')
"
# Su macchina air-gap:
pip install --no-index --find-links wheelhouse/ ctranslate2 sentencepiece langdetect
# Copia models/ dalla macchina connessa
```

> ⚠️ `ctranslate2` può anche convertire i modelli Marian nel formato CT2 per inferenza più veloce:
> `ct2-opus-mt-converter --model Helsinki-NLP/opus-mt-it-en --output_dir models/translation/opus-mt-it-en`

---

## TimeSeries Engine

### Architettura

```
TimeSeriesEngine
├── record()            → INSERT INTO metrics (DuckDB)
├── query()             → bucket aggregation (time_bucket / fallback)
├── detect_anomalies()  → Z-score rolling
├── trend_slope()       → linear regression (puro Python)
└── list_metrics()      → DISTINCT metric names
```

### Bucket aggregation

Prima tenta `time_bucket()` nativo DuckDB; se non disponibile usa il fallback Python basato su epoch-modulo.

### Anomaly detection

Z-score: `z = |x - μ| / σ`. Soglia configurabile (default `2.5`). Restituisce `(timestamp, value, z_score)` per ogni punto anomalo.

### Trend slope

Regressione lineare pura Python: `slope = Σ(xi - x̄)(yi - ȳ) / Σ(xi - x̄)²`. Unità: valore/secondo.

---

## Log Engine

### Architettura

```
LogEngine
├── query()               → SELECT con filtri (level, source, since, until)
├── tail()                → SELECT ... ORDER BY ts DESC LIMIT n
├── ingest()              → INSERT singola entry
├── ingest_file()         → bulk JSONL o plain text
├── severity_histogram()  → GROUP BY level
├── top_sources()         → GROUP BY source ORDER BY count DESC
└── detect_patterns()     → regex rules sui log recenti
```

### AegisLogSink

Processore structlog che intercetta ogni log di sistema e lo persiste in DuckDB via `LogEngine.ingest()`. Usa `loop.create_task()` per non bloccare il thread di logging. Se non c'è loop attivo (startup), salta silenziosamente.

### Pattern detection

Regole built-in: `OutOfMemory`, `ConnectionRefused`, `Traceback`, `SlowQuery`, `AuthFailure`. Estendibili senza riavvio tramite Admin Studio (FASE 7).

---

## Integrazione con Intent Engine (FASE 4)

Le modalità `timeseries` e `log_analysis` del `ModeRouter` ora ricevono le istanze concrete:

```python
router = ModeRouter(
    flags={...},
    ts_engine=TimeSeriesEngine(),
    log_engine=LogEngine(),
)
```

### Memory nelle modalità conversazionali

Ogni risposta delle modalità `conversation`, `qa`, `rag` può essere persistita in `MemoryEngine`:

```python
await memory_engine.append(MemoryEntry(session_id, "user", user_input))
result = await router.run(request)
await memory_engine.append(MemoryEntry(session_id, "assistant", result.output))
```

---

## Test coverage

| File | Classi | Test |
|---|---|---|
| `test_memory_engine.py` | `TestMemoryEngine` | 8 |
| `test_translation_engine.py` | `TestTranslationEngine`, `TestLangDetect` | 9 |
| `test_timeseries_engine.py` | `TestTimeSeriesEngine` | 6 |
| `test_log_engine.py` | `TestLogEngine` | 7 |

Totale: **30 test unitari**, tutti senza dipendenze di rete.
