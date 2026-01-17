"""API layer - presentation layer."""

from __future__ import annotations

from arch_layer_prod_mongo_fast.api.dependencies import (
    get_elastic_repo,
    get_mongo_repo,
    get_product_service,
    get_redis_repo,
)
from arch_layer_prod_mongo_fast.api.routes import router

__all__ = [
    "get_elastic_repo",
    "get_mongo_repo",
    "get_product_service",
    "get_redis_repo",
    "router",
]
