# Fase 2 — DB Layer: Persistenza Locale

## Principi

- **Air-gapped**: SQLite locale (`data/aegis.db`), nessun server DB, nessuna connessione remota.
- **Async-first**: `aiosqlite` + `SQLModel` + `sqlalchemy[asyncio]` — zero blocking I/O nel thread event loop.
- **Repository pattern**: ogni entità di dominio ha un repository dedicato che isola il codice applicativo dall'ORM.
- **Alembic migrations**: `alembic upgrade head` applica le migrazioni in ordine; `render_as_batch=True` garantisce compatibilità con SQLite per `ALTER TABLE`.

## Schema ER (16 tabelle)

```
permissions  ──< roles (permissions_json)  ──< users (role_ids_json)
assistants (owner_id → users.id)
categories (parent_id → self)
documents (owner_id → users.id)
knowledge_bases (owner_id → users.id)
memory_entries (session_id, assistant_id, user_id)
model_records
datasets (owner_id → users.id)
workflows (owner_id → users.id)
rules (owner_id → users.id)
audit_logs [APPEND-ONLY]
backups
config_entries (scope, key)
```

Note: le FK sono modellate come `String` (UUID) senza FK constraint esplicita — SQLite non enforza FK a meno di `PRAGMA foreign_keys = ON`. Il constraint viene aggiunto in migrazioni future se necessario.

## Struttura file

```
backend/
├── infrastructure/
│   ├── database/
│   │   ├── engine.py          # Singleton engine, get_session(), create_all_tables()
│   │   ├── models.py          # 16 SQLModel table=True classes
│   │   └── mappers.py         # Domain entity ↔ ORM model conversions
│   ├── db/
│   │   └── __init__.py        # Shim: re-export get_async_session per Fase 6
│   ├── migrations/
│   │   ├── alembic.ini
│   │   ├── env.py             # Async Alembic runner
│   │   ├── script.py.mako
│   │   └── versions/
│   │       └── 0001_initial_schema.py
│   └── adapters/
│       └── repositories/      # SQLiteXxxRepository per ogni entità
```

## Comandi operativi

```bash
# Prima installazione (air-gapped, dopo wheelhouse setup)
pip install alembic aiosqlite sqlmodel sqlalchemy[asyncio]

# Applicare migrations
alembic -c backend/infrastructure/migrations/alembic.ini upgrade head

# Creare nuova migration
alembic -c backend/infrastructure/migrations/alembic.ini \
  revision --autogenerate -m "descrizione_cambiamento"

# Rollback 1 step
alembic -c backend/infrastructure/migrations/alembic.ini downgrade -1
```

## Dipendenze aggiunte a requirements/base.txt

```
alembic>=1.13,<2
aiosqlite>=0.19,<1
```
