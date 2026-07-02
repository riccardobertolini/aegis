# UI Pages — Admin Studio

Reference documentation for the pages available in the Aegis Admin Studio frontend (`admin-studio/`).

---

## Overview

| Route | Component | Description |
|---|---|---|
| `/` → `/dashboard` | `DashboardPage` | System overview, KPI cards, recent activity |
| `/inference` | `InferencePage` | Interactive text-generation playground |
| `/documents` | `DocumentPage` | Upload, index and manage RAG documents |
| `/memory` | `MemoryPage` | Browse, filter and flush session memory entries |
| `/models` | `ModelsPage` | Registered model list, integrity status, load/unload |
| `/training` | `TrainingPage` | Fine-tuning job queue, dataset selection, progress |
| `/assistants` | `AssistantsPage` | Create and configure assistant personas |
| `/knowledge` | `KnowledgePage` | Knowledge-base management (RAG chunks, embeddings) |
| `/plugins` | `PluginsPage` | Plugin registry, enable/disable, config |
| `/users` | `UsersPage` | User management (RBAC) |
| `/roles` | `RolesPage` | Role editor and permission matrix |
| `/sessions` | `SessionsPage` | Active JWT session viewer and revocation |
| `/audit` | `AuditPage` | Tamper-evident audit log viewer |
| `/backup` | `BackupPage` | Encrypted backup creation and restore |
| `/monitoring` | `MonitoringPage` | Live metrics: latency, throughput, GPU/CPU |
| `/settings` | `SettingsPage` | Global system settings |
| `/feature-toggles` | `FeatureTogglesPage` | Runtime feature flags |

---

## InferencePage

**Route:** `/inference`  
**Component:** `admin-studio/src/pages/InferencePage.tsx`

### Layout

Two-column layout at ≥ 768 px:

- **Left — Editor panel** (flex-grow): Multi-line prompt textarea, output area with token/ms badge.
- **Right — Parameters sidebar** (fixed width, sticky): Sliders for Temperature, Top-p, Repetition Penalty, Max Tokens; model selector dropdown; Generate / Stop buttons.

### Key behaviours

- Generate button calls `POST /api/inference/generate` with `{ prompt, temperature, top_p, repetition_penalty, max_new_tokens, model_id }`.
- While generating the button label changes to *Stop* and disables the prompt textarea.
- Output appears in a `<pre>` block tagged with `data-testid="inference-output"`. Token count and wall-clock latency are shown as inline badges.
- Errors are surfaced inline below the output area (not as toasts).

### API contract (expected)

```
POST /api/inference/generate
Body:  { prompt: string, temperature: float, top_p: float,
         repetition_penalty: float, max_new_tokens: int, model_id: string }
Reply: { text: string, tokens_generated: int, latency_ms: int }
```

---

## DocumentPage

**Route:** `/documents`  
**Component:** `admin-studio/src/pages/DocumentPage.tsx`

### Layout

- **Toolbar row**: search input + *Upload* button.
- **Dropzone**: drag-and-drop area (accepts PDF, TXT, DOCX, MD). Clicking opens the native file picker.
- **Documents table**: Name · Size · Status · Chunks · Actions.

### Statuses

| Value | Badge colour | Meaning |
|---|---|---|
| `pending` | grey | Uploaded, not yet indexed |
| `indexing` | amber | Chunking + embedding in progress |
| `indexed` | green | Ready for RAG retrieval |
| `error` | red | Indexing failed |

### Actions per row

- **Index** — triggers `POST /api/documents/{id}/index` (only shown for `pending` / `error` rows).
- **Delete** — `DELETE /api/documents/{id}` with confirmation dialog.

### API contract (expected)

```
GET    /api/documents                  → DocumentList
POST   /api/documents          (form)  → Document
POST   /api/documents/{id}/index       → { status: "indexing" }
DELETE /api/documents/{id}             → 204
```

---

## MemoryPage

**Route:** `/memory`  
**Component:** `admin-studio/src/pages/MemoryPage.tsx`

### Layout

- **Stats bar**: Total entries · Total tokens · Active sessions (cards with `data-testid="stat-card"`).
- **Filter row**: `session_id` text input + *Apply* button.
- **Memory table**: Session ID · Role · Content (truncated to 120 chars) · Timestamp · Tokens.
- **Pagination**: previous / next controls at the bottom.
- **Flush buttons**: *Flush Session* (scoped) and *Flush All* (destructive, guarded by confirmation dialog).

### API contract (expected)

```
GET    /api/memory?session_id=&page=&per_page=  → MemoryPage
DELETE /api/memory?session_id={id}              → { deleted: int }
DELETE /api/memory                              → { deleted: int }
```

---

## Routing

All routes are declared in `admin-studio/src/App.tsx` using React Router v6 `<Routes>` / `<Route>` elements.
The sidebar navigation is defined in `admin-studio/src/components/Sidebar.tsx` via the `NAV_ITEMS` constant.

Verification tests live in:

- `tests/unit/test_routing.py` — checks that App.tsx declares all three routes and imports the page components.
- `tests/unit/test_sidebar_nav.py` — checks that Sidebar.tsx exposes the correct `href` values and labels.
- `tests/e2e/test_inference_page.py` — Playwright smoke tests for `/inference`.
- `tests/e2e/test_document_page.py` — Playwright smoke tests for `/documents`.
- `tests/e2e/test_memory_page.py` — Playwright smoke tests for `/memory`.
