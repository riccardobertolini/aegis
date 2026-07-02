# Aegis — Persistenza Locale (Fase 2)

Tutti i dati risiedono **esclusivamente su disco locale**.
Nessun DB cloud, nessuna connessione remota, nessuna telemetria.

---

## Schema Entità

| Tabella | Descrizione |
|---|---|
| `role` | Ruoli applicativi (admin, editor, viewer…) |
| `permission` | Permessi granulari per risorsa/azione per ruolo |
| `user` | Utenti locali con password hashata (bcrypt) |
| `assistant` | Assistenti AI; system-prompt e config cifrati a riposo |
| `knowledgebase` | Knowledge base tematiche |
| `category` | Categorie gerarchiche (self-referential FK) |
| `document` | Documenti caricati; integrità via SHA-256 |
| `aegismodel` | Modelli Mamba/SSM copiati manualmente in `models/` |
| `dataset` | Dataset per fine-tuning locali |
| `memorychunk` | Chunk di memoria per assistente/utente, contenuto cifrato |
| `version` | Snapshot versioni (assistants, models, documents) |
| `workflow` | Definizioni workflow in JSON |
| `backuprecord` | Registro backup cifrati |
| `auditlogentry` | Log di audit immutabile con indici su actor/action/time |

---

## Migrazioni

Gestite da **Alembic** con supporto `render_as_batch=True` per SQLite.

```bash
# Prima migrazione (schema completo)
alembic -c backend/infrastructure/db/migrations/alembic.ini upgrade head

# Generare una nuova revisione
alembic -c backend/infrastructure/db/migrations/alembic.ini revision --autogenerate -m "descrizione"

# Rollback
alembic -c backend/infrastructure/db/migrations/alembic.ini downgrade -1
```

> ⚠️  `alembic.ini` non contiene `sqlalchemy.url`; la URL viene letta
> da `Settings.database_url` (`.env` o variabile d'ambiente) tramite `env.py`.

---

## Repository Pattern

Ogni entità ha:
1. **Port** (ABC) in `backend/domain/ports/repository.py`
2. **Implementazione concreta** in `backend/infrastructure/adapters/repositories/`

Tutti i metodi sono `async`; la sessione viene iniettata dall'esterno (dependency injection).

```python
# Esempio d'uso in un use-case
async def create_assistant(dto: AssistantCreateDTO, repo: IRepository, session: AsyncSession):
    assistant = Assistant(**dto.dict())
    return await repo.create(assistant, session)
```

---

## Storage Locale

```
data/
├── db/
│   └── aegis.db              # SQLite principale
├── documents/                # Documenti caricati
│   └── <sha256[:2]>/<sha256[2:]>_<filename>
├── models/                   # Modelli copiati manualmente
│   └── <model_name>/
├── embeddings/               # Vettori ChromaDB
├── logs/                     # structlog JSON rotating
└── backups/                  # Backup cifrati .aegbak

keys/
└── aegis_master.key          # Chiave AES-256-GCM (generata al primo avvio)
```

L'integrità dei file è verificata tramite SHA-256 ad ogni lettura (`StorageManager.verify_integrity`).

---

## Cifratura a Riposo

- **Algoritmo**: AES-256-GCM
- **Libreria**: `cryptography` (PyCA) — pura Python, zero dipendenze native
- **Chiave**: derivata con PBKDF2-HMAC-SHA256 o caricata da `keys/aegis_master.key`
- **Ambiti cifrati**:
  - `assistant.system_prompt_enc`, `assistant.config_enc`
  - `memorychunk.content_enc`
  - Tutti i backup (`.aegbak`)
  - File documenti su richiesta (`encrypt=True`)

---

## Config Management

`ConfigManager` legge `config/global.json.enc` (cifrato) e supporta:

- **Override per assistente**: `config/assistant.<id>.json.enc`
- **Feature flags**: `{"feature_flags": {"speech": true, "translation": false}}`
- **Lookup con fallback**: `get_for_assistant(key, assistant_id)` → override → globale → default

---

## Backup

```bash
# Backup manuale via API (implementata in Fase 3)
POST /api/v1/admin/backup

# Restore
POST /api/v1/admin/backup/restore  {"path": "/data/backups/2026-07-02T11_00_00.aegbak"}
```

I backup sono file `.aegbak` cifrati con AES-256-GCM. Contengono un JSON con:
- Dump completo del DB SQLite
- Configurazioni (già cifrate)
- Metadati (timestamp, versione schema)

---

## Test

```bash
# Solo unit
pytest tests/unit/ -v

# Solo integration (richiedono aiosqlite)
pytest tests/integration/ -v

# Tutto
pytest --tb=short
```

I test di integrazione usano un SQLite **in-memory** (`sqlite+aiosqlite:///:memory:`).
Nessun file viene creato su disco.
