# Contributing to Aegis

## Branch Strategy

```
main        — stable, tagged releases only
develop     — integration branch
feature/*   — individual features (branch from develop)
fix/*       — bug fixes (branch from develop)
release/*   — release preparation (branch from develop, merge into main+develop)
```

## Commit Convention (Conventional Commits)

```
feat:     new feature
fix:      bug fix
docs:     documentation only
style:    formatting, no logic change
refactor: neither fix nor feature
test:     adding/updating tests
chore:    tooling, deps, CI
perf:     performance improvement
```

Example: `feat(inference): add Mamba SSM inference port implementation`

## Code Standards

- **Architecture**: Clean / Hexagonal — domain never imports infra
- **DI**: constructor injection, never service-locator globals
- **SOLID**: single responsibility per class, interfaces via `abc.ABC`
- **Error handling**: typed exceptions in `backend/shared/exceptions.py`, never bare `except:`
- **Logging**: structured JSON via `structlog`, local file sink only, no external sinks
- **Config**: `pydantic-settings` + `.env` file; secrets via local encrypted vault (`backend/security`)
- **Tests**: every module has a companion `tests/unit/` file; coverage target ≥ 80%

## Pre-commit Hooks

```bash
pip install pre-commit
pre-commit install
```

Hooks: `black`, `ruff`, `mypy`, `pytest --co -q` (collect-only).

## Pull Request Checklist

- [ ] Tests added / updated
- [ ] Docstrings on public symbols
- [ ] No new HTTP calls to external hosts
- [ ] `CHANGELOG.md` entry added
