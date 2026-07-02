# Testing Strategy

## Layers

| Layer | Tool | Location | Scope |
|---|---|---|---|
| Unit | pytest | `tests/unit/` | Pure-Python logic: engines, services, models |
| Integration | pytest + httpx | `tests/integration/` | FastAPI routes against in-memory SQLite |
| E2E | pytest-playwright | `tests/e2e/` | Browser smoke tests against live dev server |

## Running tests

```bash
# All unit + integration tests
pytest tests/unit tests/integration -v

# E2E tests (requires running dev server)
cd admin-studio && npm run dev &
pytest tests/e2e/ --base-url=http://localhost:5173 -v
```

## Unit test structure

```
tests/unit/
  test_config.py                 # shared config loading
  test_exceptions.py             # exception hierarchy
  test_ports_contracts.py        # ABC contracts for all ports
  test_routing.py                # App.tsx route declarations
  test_sidebar_nav.py            # Sidebar NAV_ITEMS hrefs + labels
  test_inference_engine.py       # InferenceEngine logic
  test_memory_engine.py          # MemoryEngine CRUD
  test_document_engine.py        # DocumentEngine indexing flow
  test_core_ai_service.py        # CoreAIService orchestration
  test_mode_router.py            # ModeRouter dispatch
  security/                      # Argon2, JWT, RBAC, AES, audit …
  inference/                     # Inference-specific sub-tests
  memory/                        # Memory-specific sub-tests
  document/                      # Document-specific sub-tests
  rag/                           # RAG retrieval sub-tests
  training/                      # Training pipeline sub-tests
```

## E2E test scope (Push 11c)

Smoke tests added for the three pages introduced in Push 11b:

| Page | Test file | Checks |
|---|---|---|
| InferencePage | `test_inference_page.py` | Renders, sidebar active, textarea, sliders × 3, generate shows output |
| DocumentPage | `test_document_page.py` | Renders, sidebar active, dropzone, table headers (Name/Status), search input |
| MemoryPage | `test_memory_page.py` | Renders, sidebar active, stat cards ≥ 2, session filter, flush button |

## CI integration

Unit and integration tests run on every push via GitHub Actions (`.github/workflows/ci.yml`).
E2E tests run in a separate job that spins up the Vite dev server before executing Playwright.

## Coverage target

- Unit: ≥ 80 % line coverage on `backend/`
- E2E: 100 % of pages reachable via sidebar must have a smoke test
