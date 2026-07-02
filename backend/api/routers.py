"""Central router registry — imports and mounts all sub-routers."""
from fastapi import FastAPI


def register_routers(app: FastAPI) -> None:
    from backend.api.inference_router import router as inference_router

    app.include_router(
        inference_router,
        prefix="/api/v1/inference",
        tags=["inference"],
    )

    # Security router (Phase 6) — mount if available
    try:
        from backend.api.security_router import router as security_router  # type: ignore
        app.include_router(
            security_router,
            prefix="/api/v1/security",
            tags=["security"],
        )
    except ImportError:
        pass
