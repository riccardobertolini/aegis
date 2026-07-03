"""Central router registry — registers ALL API routers on the FastAPI app."""
from fastapi import FastAPI


def register_routers(app: FastAPI) -> None:
    # ── routers/  (small focused routers in the routers sub-package) ──────────
    from backend.api.admin_router import router as admin_router
    from backend.api.document_router import router as document_router

    # ── top-level routers (richer, self-contained) ────────────────────────────
    from backend.api.inference_router import router as inference_router
    from backend.api.memory_router import router as memory_flat_router
    from backend.api.plugin_router import router as plugin_router
    from backend.api.routers.documents import router as documents_router
    from backend.api.routers.intent import router as intent_router
    from backend.api.routers.knowledge import router as knowledge_router
    from backend.api.routers.logs import router as logs_router
    from backend.api.routers.memory import router as memory_router
    from backend.api.routers.timeseries import router as timeseries_router
    from backend.api.routers.translation import router as translation_router
    from backend.api.security_router import router as security_router
    from backend.api.speech_router import router as speech_router
    from backend.api.training_router import router as training_router

    # inference: mount under /api/v1/inference  and  /api/v1/ai
    app.include_router(inference_router, prefix="/api/v1/inference")
    app.include_router(inference_router, prefix="/api/v1/ai")  # alias for /chat

    # documents / RAG  (prefix already set in router: /api/v1/documents)
    app.include_router(document_router)

    # training  (prefix: /training)
    app.include_router(training_router)

    # admin  (prefix: /admin)
    app.include_router(admin_router)

    # security  (prefix: /security)
    app.include_router(security_router)

    # speech  — register with prefix if not already set
    app.include_router(speech_router)

    # plugins
    app.include_router(plugin_router)

    # small routers (each declares its own prefix)
    app.include_router(intent_router)
    app.include_router(memory_router)
    app.include_router(memory_flat_router)
    app.include_router(translation_router)
    app.include_router(timeseries_router)
    app.include_router(logs_router)
    app.include_router(knowledge_router)
    app.include_router(documents_router)
