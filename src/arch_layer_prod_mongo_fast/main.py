"""FastAPI application entry point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from beanie import init_beanie
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient

from arch_layer_prod_mongo_fast.api.routes import router
from arch_layer_prod_mongo_fast.config import get_settings
from arch_layer_prod_mongo_fast.logging_config import setup_logging
from arch_layer_prod_mongo_fast.middleware import RequestLoggingMiddleware
from arch_layer_prod_mongo_fast.models.product import Product

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

logger = logging.getLogger("arch_layer_prod_mongo_fast.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:  # noqa: ARG001
    """Application lifespan: startup and shutdown."""
    settings = get_settings()

    # Configure logging (JSON in prod, readable in dev)
    setup_logging(
        level=settings.log_level,
        json_format=settings.environment != "development",
        log_file=settings.log_file,
    )
    logger.info("Application starting", extra={"environment": settings.environment})

    client: AsyncIOMotorClient = AsyncIOMotorClient(settings.mongodb_uri)  # type: ignore[type-arg]
    database = client[settings.mongodb_database]

    await init_beanie(database=database, document_models=[Product])  # type: ignore[arg-type]
    logger.info("MongoDB initialized", extra={"database": settings.mongodb_database})

    yield

    logger.info("Application shutting down")
    client.close()


app = FastAPI(
    title="Layered Architecture Demo",
    description="Production layered architecture with MongoDB, Redis, Elasticsearch",
    version="0.1.0",
    lifespan=lifespan,
)

# Middleware (order matters: first added = outermost)
app.add_middleware(RequestLoggingMiddleware)

app.include_router(router)


@app.get("/", tags=["health"])
async def root() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "message": "Layered Architecture API"}


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    """Detailed health check."""
    return {"status": "healthy", "service": "arch-layer-prod-mongo-fast"}
