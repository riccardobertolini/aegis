# Coding Conventions

## Naming

- **Files/modules**: `snake_case.py`
- **Classes**: `PascalCase`
- **Interfaces/Ports**: prefix `I` — e.g. `IInferencePort`
- **Implementations**: suffix with adapter name — e.g. `MambaInferenceAdapter`
- **Use cases**: `VerbNounUseCase` — e.g. `RunInferenceUseCase`
- **Exceptions**: suffix `Error` — e.g. `ModelNotFoundError`
- **Constants**: `UPPER_SNAKE_CASE`
- **React components**: `PascalCase.tsx`
- **React hooks**: `useHookName.ts`

## Error Handling

```python
# GOOD — typed domain exception, logged at boundary
raise ModelNotFoundError(model_id=model_id)

# BAD — bare except, swallowed error
try:
    ...
except:
    pass
```

All domain exceptions extend `AegisBaseError` from `backend/shared/exceptions.py`.
FastAPI exception handlers in `backend/api/exception_handlers.py` translate domain errors to HTTP responses.

## Logging

```python
import structlog
log = structlog.get_logger(__name__)

log.info("inference.started", model_id=model_id, prompt_tokens=n)
log.error("inference.failed", model_id=model_id, error=str(e))
```

- Always structured JSON
- Local file sink only — never remote
- Log rotation via `logging.handlers.RotatingFileHandler`
- Log levels: `DEBUG` (dev), `INFO` (prod), `WARNING`/`ERROR` always logged

## Config Management

- All config via `pydantic-settings` `Settings` class
- Source: environment variables > `.env` file > defaults
- One singleton `get_settings()` function with `@lru_cache`
- Secrets (keys, passwords) stored in local encrypted vault, not in `.env`

## Dependency Injection

```python
# Port (interface) — in domain layer
class IInferencePort(ABC):
    @abstractmethod
    async def run(self, request: InferenceRequest) -> InferenceResponse: ...

# Adapter — in infra layer
class MambaInferenceAdapter(IInferencePort):
    async def run(self, request: InferenceRequest) -> InferenceResponse:
        ...

# Use case — receives port via constructor
class RunInferenceUseCase:
    def __init__(self, inference_port: IInferencePort) -> None:
        self._port = inference_port
```

FastAPI `Depends()` wires adapters to ports at the interface layer.
