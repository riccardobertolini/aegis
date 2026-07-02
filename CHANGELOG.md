# Changelog

All notable changes follow [Conventional Commits](https://www.conventionalcommits.org/).

## [Unreleased]

### Added
- PHASE 0: Global architecture diagram (Mermaid)
- Complete monorepo directory skeleton
- Abstract Port interfaces for all 14 engines (Hexagonal Architecture)
- `pyproject.toml`, requirements strategy, `.gitignore`, `.env.example`
- `README.md`, `CONTRIBUTING.md`, `LICENSE` (MIT)
- `docs/architecture/`, `docs/testing_strategy.md`
- `backend/shared`: config, logging, exceptions
- `backend/domain/ports`: all port contracts
- `backend/infrastructure/adapters`: placeholder (implemented in later phases)
- Initial unit tests: config, exceptions, port contracts
- Pre-commit hooks: black, ruff, mypy, pytest collect
