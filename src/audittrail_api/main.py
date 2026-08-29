"""FastAPI application factory."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from audittrail_api import __version__
from audittrail_api.api.errors import install_error_handlers
from audittrail_api.api.middleware import request_context_middleware
from audittrail_api.api.router import router as api_router
from audittrail_api.config import Settings, get_settings
from audittrail_api.database.session import close_database, create_schema
from audittrail_api.health.router import router as health_router
from audittrail_api.logging import configure_logging


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build an isolated application instance for production or tests."""

    runtime_settings = settings or get_settings()
    configure_logging()

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        if runtime_settings.auto_create_schema:
            await create_schema()
        yield
        await close_database()

    app = FastAPI(
        title=runtime_settings.app_name,
        version=__version__,
        description="Multi-tenant ingestion and search for tamper-evident audit events.",
        lifespan=lifespan,
    )
    if runtime_settings.allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=runtime_settings.allowed_origins,
            allow_credentials=False,
            allow_methods=["GET", "POST", "PUT", "DELETE"],
            allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "X-API-Key"],
        )
    app.middleware("http")(request_context_middleware)
    install_error_handlers(app)
    app.include_router(health_router)
    app.include_router(api_router)
    return app


app = create_app()
