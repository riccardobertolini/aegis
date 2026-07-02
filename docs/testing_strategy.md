# Testing Strategy

## Layers

| Layer | Tool | Location | Target |
|---|---|---|---|
| Unit | Pytest | `tests/unit/` | ≥ 80% coverage per module |
| Integration | Pytest + HTTPX | `tests/integration/` | All API routes, DB adapters |
| E2E | Playwright (future) | `tests/e2e/` | Critical user journeys |
| Frontend Unit | Vitest + RTL | `admin-studio/src/__tests__/` | Components, hooks |
| Frontend E2E | Playwright | `tests/e2e/frontend/` | Chat flow, doc upload |

## Conventions

- Test file mirrors source: `backend/shared/config.py` → `tests/unit/test_config.py`
- Fixtures in `tests/conftest.py`
- No real network calls in tests — mock at port boundary
- Each port has a `FakeXxxAdapter` in `tests/fakes/` for use in unit tests
- Coverage enforced in CI via `--cov-fail-under=80`

## Running

```bash
# All tests
pytest

# With coverage HTML
pytest --cov-report=html

# Specific module
pytest tests/unit/test_config.py -v
```
