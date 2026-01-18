"""Request logging middleware with automatic request_id propagation."""

from __future__ import annotations

import logging
import time
import uuid
from typing import TYPE_CHECKING

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from arch_layer_prod_mongo_fast.logging_config import request_context

if TYPE_CHECKING:
    from starlette.requests import Request
    from starlette.responses import Response

logger = logging.getLogger("arch_layer_prod_mongo_fast.middleware")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that logs requests and propagates request_id."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """Process request with logging and context propagation.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in chain

        Returns:
            HTTP response
        """
        # Generate or extract request_id from header
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])

        # Set context for this request (available in all logs)
        ctx = {
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
        }
        token = request_context.set(ctx)

        start_time = time.perf_counter()

        logger.info(
            "Request started",
            extra={
                "query_params": str(request.query_params),
                "client_host": request.client.host if request.client else None,
            },
        )

        try:
            response: Response = await call_next(request)
            duration_ms = (time.perf_counter() - start_time) * 1000

            logger.info(
                "Request completed",
                extra={
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                },
            )

            # Add request_id to response headers for tracing
            response.headers["X-Request-ID"] = request_id

        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.exception(
                "Request failed",
                extra={
                    "error": str(e),
                    "duration_ms": round(duration_ms, 2),
                },
            )
            raise

        else:
            return response

        finally:
            # Reset context
            request_context.reset(token)
