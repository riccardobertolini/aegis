# Changelog

All notable changes to this project will be documented in this file.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added — Push 11c: Sidebar/routing tests + e2e smoke tests + docs

#### Tests — Unit
- `tests/unit/test_routing.py`: Verifies that `App.tsx` declares routes `/inference`, `/documents`, `/memory` and imports the three page components
- `tests/unit/test_sidebar_nav.py`: Verifies `Sidebar.tsx` exposes correct `href` values and human-readable labels for the three new pages

#### Tests — E2E (Playwright)
- `tests/e2e/conftest.py`: Shared Playwright fixtures (browser, context, page — session-scoped browser for speed)
- `tests/e2e/test_inference_page.py`: 6 smoke tests — renders, sidebar active, textarea present, 3 sliders, generate reveals output
- `tests/e2e/test_document_page.py`: 5 smoke tests — renders, sidebar active, dropzone attached, table headers (Name/Status), search input
- `tests/e2e/test_memory_page.py`: 5 smoke tests — renders, sidebar active, stat cards ≥ 2, session filter, flush button

#### Documentation
- `docs/ui-pages.md`: Full reference for all Admin Studio pages — routes, component paths, layouts, key behaviours, API contracts
- `docs/testing_strategy.md`: Updated with E2E layer, new unit test files, CI integration notes, coverage targets

---

### Added — Push 11b: Nuove pagine InferencePage, DocumentPage, MemoryPage

#### Frontend
- `admin-studio/src/pages/InferencePage.tsx` + `InferencePage.module.css`: Two-column inference playground with sliders (temperature, top-p, repetition penalty, max tokens), model selector, output with token/ms badges
- `admin-studio/src/pages/DocumentPage.tsx` + `DocumentPage.module.css`: Drag-and-drop upload, indexing status table, per-row Index/Delete actions, search toolbar
- `admin-studio/src/pages/MemoryPage.tsx` + `MemoryPage.module.css`: Stats bar, paginated memory table, session filter, flush-session and flush-all with confirmation
- `admin-studio/src/App.tsx`: Routes added for `/inference`, `/documents`, `/memory`
- `admin-studio/src/components/Sidebar.tsx`: NAV_ITEMS updated with Documents, Inference, Memory + SVG icons

---

### Added — Phase 6: Security Engine

#### Domain
- Extended `ISecurityPort` with 22 granular `Permission` enum values across 8 domains
- Added `DEFAULT_ROLES` dict (superadmin, admin, operator, viewer)
- New domain models: `ModelIntegrityResult`, `AuditEntry` dataclasses
- `AuthToken` extended with `session_id` field
- `UserPrincipal` extended with `permissions` field
- `AuthenticationError`, `AuthorizationError`, `IntegrityError`, `BackupError` added to exception hierarchy

#### Infrastructure — `backend/infrastructure/security/`
- `models.py`: SQLModel tables for users, roles, sessions, audit log, encryption keys, model hashes
- `password.py`: Argon2id hashing (argon2-cffi) — time_cost=3, memory=64 MiB
- `token.py`: Local HS256 JWT creation + verification (PyJWT)
- `encryption.py`: AES-256-GCM `LocalKeyStore` with PBKDF2-derived master key, key rotation, kid-prefix ciphertext
- `rbac.py`: `RBACEnforcer` — stateless permission resolver with custom role support
- `audit.py`: `AuditWriter` (HMAC-SHA256 chained rows) + `AuditReader` with chain verification
- `integrity.py`: `ModelIntegrityService` — SHA-256 file hash registration and verification
- `backup.py`: `BackupService` — AES-256-GCM tar archives (`.aeb` format)
- `service.py`: `SecurityService` — concrete implementation of `ISecurityPort`, all engines composed
- `dependencies.py`: FastAPI `Depends` helpers (`get_current_user`, `require_permission`)
- `seeder.py`: First-run bootstrap for default roles and superadmin
- `container.py`: DI container factory (`build_security_container`)

#### API
- `api/security_router.py`: REST endpoints — auth login/logout, sessions, audit query, model integrity, key rotation, backup
- `api/middleware/security_middleware.py`: Request-level Bearer token extraction + security response headers

#### Configuration
- `shared/config.py`: Added `jwt_secret_key`, `jwt_expiry_minutes`, `security_keystore_path`, `security_keystore_passphrase`, `security_backup_passphrase`, `backup_dir`
- `.env.example`: Updated with all new security variables and generation instructions

#### Tests
- `tests/unit/security/test_password.py`: Argon2id hash/verify/needs_rehash
- `tests/unit/security/test_token.py`: JWT create/decode/expire/tamper
- `tests/unit/security/test_rbac.py`: Role resolution, permission union, custom roles
- `tests/unit/security/test_encryption.py`: AES-256-GCM roundtrip, rotation, persistence
- `tests/unit/security/test_audit.py`: Append, query, HMAC chain verification
- `tests/unit/security/test_integrity.py`: Hash registration, tamper detection
- `tests/unit/security/test_backup.py`: Create, restore, wrong passphrase, invalid magic

#### Documentation
- `docs/security/threat_model.md`: Full STRIDE analysis, asset classification, residual risks
- `docs/security/hardening.md`: OS hardening, systemd unit, filesystem permissions, key rotation, Secure Boot (optional)
- `docs/security/compliance_checklist.md`: ISO 27001 / NIST SP 800-53 / GDPR Art. 25–32 mapping

#### Dependencies
- `requirements/base.txt`: Added `argon2-cffi`, `PyJWT`, `cryptography`
- `requirements/dev.txt`: Added `pytest-asyncio`, `httpx`

---

## [0.1.0] — Phase 0

### Added
- Monorepo scaffold: `backend/`, `admin-studio/`, `client/`, `packaging/`, `docs/`, `tests/`
- Clean Architecture skeleton: domain ports (14 engines), FastAPI app factory, shared config/logging/exceptions
- 14 `IXxxPort` abstract base classes in `backend/domain/ports/`
- `requirements/base.txt`, `requirements/ml.txt`, `requirements/dev.txt`
- `pyproject.toml`, `.pre-commit-config.yaml`, `.gitignore`, `.env.example`
- Architecture docs: `overview.md`, `conventions.md`, `offline_setup.md`, `testing_strategy.md`
- Base unit tests: `test_config.py`, `test_exceptions.py`, `test_ports_contracts.py`
- `README.md`, `CONTRIBUTING.md`, `LICENSE (MIT)`, `CHANGELOG.md`
