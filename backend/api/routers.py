"""Central router registration."""
from fastapi import FastAPI


def register_routers(app: FastAPI) -> None:
    """Register all API routers. Implemented per-phase."""
    # Routers will be registered here as engines are implemented.
    # Example:
    # from backend.api.v1 import inference, knowledge, memory
    # app.include_router(inference.router, prefix="/api/v1/inference")
    pass
