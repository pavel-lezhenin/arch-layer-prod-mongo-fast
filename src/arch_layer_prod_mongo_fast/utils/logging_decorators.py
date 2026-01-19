"""Logging decorators for service and repository methods."""

from __future__ import annotations

import logging
import time
from functools import wraps
from typing import TYPE_CHECKING, ParamSpec, TypeVar

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

P = ParamSpec("P")
R = TypeVar("R")


def log_operation(
    operation: str,
    *,
    log_args: bool = False,
    log_result: bool = False,
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    """Decorator that logs async method execution with timing.

    Args:
        operation: Name of the operation for logging
        log_args: Whether to log function arguments (default: False)
        log_result: Whether to log return value (default: False)

    Returns:
        Decorated async function with logging

    Example:
        @log_operation("Create product")
        async def create(self, data: ProductCreate) -> Product:
            ...
    """

    def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        logger = logging.getLogger(f"arch_layer_prod_mongo_fast.{func.__module__}")

        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            extra: dict[str, object] = {"operation": operation}

            if log_args and kwargs:
                # Filter out sensitive data
                safe_kwargs = {
                    k: v
                    for k, v in kwargs.items()
                    if k not in ("password", "secret", "token", "api_key")
                }
                extra["call_args"] = safe_kwargs

            logger.debug("%s started", operation, extra=extra)
            start_time = time.perf_counter()

            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.perf_counter() - start_time) * 1000

                extra["duration_ms"] = round(duration_ms, 2)
                if log_result and result is not None:
                    extra["result_type"] = type(result).__name__

            except Exception as e:
                duration_ms = (time.perf_counter() - start_time) * 1000
                extra["duration_ms"] = round(duration_ms, 2)
                extra["error"] = str(e)
                extra["error_type"] = type(e).__name__

                logger.warning("%s failed", operation, extra=extra)
                raise

            else:
                logger.info("%s completed", operation, extra=extra)
                return result

        return wrapper

    return decorator


def log_operation_sync(
    operation: str,
    *,
    log_args: bool = False,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator that logs sync method execution with timing.

    Args:
        operation: Name of the operation for logging
        log_args: Whether to log function arguments

    Returns:
        Decorated sync function with logging
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        logger = logging.getLogger(f"arch_layer_prod_mongo_fast.{func.__module__}")

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            extra: dict[str, object] = {"operation": operation}

            if log_args and kwargs:
                extra["call_args"] = kwargs

            logger.debug("%s started", operation, extra=extra)
            start_time = time.perf_counter()

            try:
                result = func(*args, **kwargs)
                duration_ms = (time.perf_counter() - start_time) * 1000
                extra["duration_ms"] = round(duration_ms, 2)

            except Exception as e:
                duration_ms = (time.perf_counter() - start_time) * 1000
                extra["duration_ms"] = round(duration_ms, 2)
                extra["error"] = str(e)
                extra["error_type"] = type(e).__name__

                logger.warning("%s failed", operation, extra=extra)
                raise

            else:
                logger.info("%s completed", operation, extra=extra)
                return result

        return wrapper

    return decorator
