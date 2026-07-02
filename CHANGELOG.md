# Changelog

All notable changes to **Aegis** are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

### Added
- Phase 2 Step 3: `backend/domain/models.py` — all 14 SQLModel table definitions
- `tests/conftest.py` — shared async fixtures (db_session, encryption, storage, backup_manager, config_manager)
- `scripts/init_local.py` — first-run air-gapped init (dirs, key, migrations, seed)
- Complete implementations for all adapters overwritten with final versions:
  `encryption.py`, `storage.py`, `backup_manager.py`, `config_manager.py`
- All repository concrete implementations consolidated (15 repos, all `async`)

## [0.2.0] - 2026-07-02

### Added
- Phase 2 Step 2: missing repositories (knowledge, dataset, role/permission, version)
- Alembic migration `0001_initial_schema` (14 tables, FK-ordered, render_as_batch)
- `backend/infrastructure/db/engine.py` — async SQLite engine factory
- `backend/infrastructure/container.py` — full DI wiring
- Integration test suites: persistence, encryption, storage, backup, config_manager
- `docs/persistence.md` — schema, migrations, storage layout, encryption spec
- `requirements/base.txt` updated with alembic, cryptography, bcrypt

## [0.1.0] - 2026-07-01

### Added
- Phase 0: Monorepo scaffold, Hexagonal Architecture ports (14 engines),
  shared config/logging/exceptions, FastAPI app factory, requirements,
  pyproject.toml, pre-commit hooks, docs, tests skeleton, LICENSE, README.
- Phase 2 Step 1: domain ports IRepository, IEncryptionPort; base SQLite
  repository; initial adapters (assistant, user, document, memory, model,
  workflow, audit, backup); encryption/storage/config/backup adapters (draft).
