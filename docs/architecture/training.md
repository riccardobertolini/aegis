# Training Engine — Fase 8

## Panoramica

Pipeline di fine-tuning completamente locale per modelli Mamba/SSM.
Nessun tracking cloud, nessun download automatico di pesi.

```
                       +------------------+
    dataset file  -->  | DatasetManager   |  versioning + iter
                       +------------------+
                               |
                       +------------------+
                       |  Preprocessor    |  tokenize + chunk
                       +------------------+
                               |
              +-------------------------------+
              |         LocalTrainer          |
              |  PyTorch loop (CPU o CUDA)    |
              | AdamW + CosineAnnealing LR   |
              +-------------------------------+
             /              |                 \
   +-----------+   +----------------+   +------------+
   |Checkpoint |   |ExperimentTrack.|   |  Evaluator |
   |  Manager  |   | (JSONL locale) |   | ppl + acc  |
   +-----------+   +----------------+   +------------+
                               |
                       +------------------+
                       |   ModelSigner    |  SHA-256 + HMAC
                       +------------------+
                               |
                       +------------------+
                       | MambaModelLoader |  re-scan → inference
                       +------------------+
```

## Componenti

| File | Responsabilità |
|---|---|
| `dataset.py` | Ingestione JSONL/CSV/TXT, versioning, iterazione |
| `preprocessor.py` | Tokenizzazione + sliding-window chunking |
| `trainer.py` | Loop PyTorch, AdamW, CosineAnnealingLR, async |
| `checkpoint.py` | Salva/carica checkpoint ogni N step |
| `experiment.py` | Tracker locale append-only (JSONL) |
| `evaluator.py` | Perplexity + token accuracy offline |
| `signer.py` | SHA-256 per file + HMAC manifesto |
| `service.py` | Implementa `ITrainingPort`, coordina tutto |
| `container.py` | DI factory |

## Dataset format

Il formato preferito è JSONL con campo `text`:

```jsonl
{"text": "Testo di training..."}
{"text": "Altro esempio..."}
```

Sono supportati anche CSV (header con colonna `text`) e TXT (una riga = un campione).

## Directory layout a runtime

```
aegis_project/
├── datasets/          # dataset versionati
│   └── my-dataset/
│       └── 20260702T210000Z/
│           ├── train.jsonl
│           ├── eval.jsonl
│           └── meta.json
├── experiments/       # metriche run
│   └── <run_id>/
│       ├── summary.json
│       └── metrics.jsonl
├── checkpoints/       # pesi checkpoint
│   └── <run_id>/
│       ├── step_000050.pt
│       └── index.json
└── models/            # modelli pronti (Fase 1)
    └── my-finetuned/
        ├── config.json
        ├── model.pt
        ├── tokenizer.json
        ├── training_info.json
        └── integrity.json   ← generato da ModelSigner
```

## Avvio di un job via API

```bash
# 1. Ingerisci il dataset
curl -X POST http://localhost:8000/training/datasets \
  -H 'Content-Type: application/json' \
  -d '{"name":"my-ds","source_path":"./data/train.jsonl","split":"train"}'

# 2. Avvia il fine-tuning
curl -X POST http://localhost:8000/training/jobs \
  -H 'Content-Type: application/json' \
  -d '{
    "base_model_id": "mamba-130m",
    "dataset_name": "my-ds",
    "output_model_id": "mamba-130m-ft",
    "epochs": 3,
    "learning_rate": 1e-4,
    "batch_size": 4
  }'

# 3. Monitora
curl http://localhost:8000/training/jobs/<job_id>

# 4. Verifica integrità modello output
curl http://localhost:8000/training/models/mamba-130m-ft/verify
```

## Configurazione `.env` aggiuntiva (Fase 8)

```env
DATASETS_DIR=datasets
EXPERIMENTS_DIR=experiments
CHECKPOINTS_DIR=checkpoints
MODEL_HMAC_SECRET=cambia-questa-stringa-con-un-segreto-lungo
```

## Dipendenze (`requirements/ml.txt`)

Nessuna nuova dipendenza oltre a PyTorch (già richiesto da Fase 1).
Se si usa mamba-ssm, il training avviene su GPU; con mamba-minimal su CPU.
