from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware

from config.settings import settings

# Import routers
from api.routes import auth as auth_routes
from api.routes import users as users_routes
from api.routes import patients as patients_routes
from api.routes import predictions as predictions_routes
from api.routes import models as models_routes
from api.routes import admin as admin_routes
from api.routes import monitoring as monitoring_routes
from api.routes import explain as explain_routes
from api.routes import clinical_ops as clinical_ops_routes

from core.logging_config import configure_logging, get_logger
from core.middleware import RequestIDMiddleware
from core.middleware import RequestSizeLimitMiddleware, RequestTimeoutMiddleware


def create_app() -> FastAPI:
    # Configure logging before app creation
    configure_logging()
    logger = get_logger("ckdci.app")

    app = FastAPI(title=settings.APP_NAME)

    # Rate limiter (default: 100/min per IP; tune via env)
    limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)

    # CORS - in production, set ALLOWED_ORIGINS environment variable to a comma-separated list
    import os
    allowed = os.getenv("ALLOWED_ORIGINS", "*")
    allow_origins = [o.strip() for o in allowed.split(",") if o.strip()] if allowed != "*" else ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request ID + tracing middleware
    app.add_middleware(RequestIDMiddleware)
    # Request size limit and per-request timeout
    app.add_middleware(RequestSizeLimitMiddleware)
    app.add_middleware(RequestTimeoutMiddleware)

    # Include routers
    app.include_router(auth_routes.router, prefix="/auth", tags=["auth"])
    app.include_router(users_routes.router)
    app.include_router(patients_routes.router)
    app.include_router(predictions_routes.router, prefix="/predictions")
    app.include_router(models_routes.router)
    app.include_router(admin_routes.router)
    app.include_router(monitoring_routes.router)
    app.include_router(explain_routes.router)
    app.include_router(clinical_ops_routes.router)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/ready")
    def ready():
        # In a full deployment, check DB connectivity, model loaded, etc.
        return {"ready": True}

    @app.exception_handler(Exception)
    async def unicorn_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception", exc_info=exc)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    @app.get("/metrics")
    def metrics():
        from core.metrics import get_metrics

        return get_metrics()

    @app.get("/metrics/prometheus")
    def metrics_prometheus():
        from fastapi.responses import PlainTextResponse
        from core.metrics import get_metrics_prometheus

        return PlainTextResponse(get_metrics_prometheus(), media_type="text/plain; version=0.0.4")

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
