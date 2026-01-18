"""Middleware package."""

from __future__ import annotations

from arch_layer_prod_mongo_fast.middleware.logging_middleware import (
    RequestLoggingMiddleware,
)

__all__ = ["RequestLoggingMiddleware"]
