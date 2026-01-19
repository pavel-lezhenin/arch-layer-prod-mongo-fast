"""Tests for request logging middleware."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock

import pytest
from starlette.requests import Request
from starlette.responses import Response

from arch_layer_prod_mongo_fast.logging_config import request_context
from arch_layer_prod_mongo_fast.middleware.logging_middleware import (
    RequestLoggingMiddleware,
)


class TestRequestLoggingMiddleware:
    """Test RequestLoggingMiddleware."""

    async def test_middleware_sets_request_context(self) -> None:
        """Test middleware sets request context for logging."""
        captured_context: dict[str, object] | None = None

        async def capture_context(request: Request) -> Response:
            nonlocal captured_context
            captured_context = request_context.get()
            return Response(content="OK")

        middleware = RequestLoggingMiddleware(app=MagicMock())

        # Create mock request
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/test",
            "query_string": b"",
            "headers": [],
        }
        request = Request(scope)

        await middleware.dispatch(request, capture_context)

        assert captured_context is not None
        assert captured_context["path"] == "/api/test"
        assert captured_context["method"] == "GET"
        assert "request_id" in captured_context

    async def test_middleware_uses_header_request_id(self) -> None:
        """Test middleware uses X-Request-ID from header if present."""
        captured_context: dict[str, object] | None = None

        async def capture_context(request: Request) -> Response:
            nonlocal captured_context
            captured_context = request_context.get()
            return Response(content="OK")

        middleware = RequestLoggingMiddleware(app=MagicMock())

        scope = {
            "type": "http",
            "method": "POST",
            "path": "/api/items",
            "query_string": b"",
            "headers": [(b"x-request-id", b"custom-id-123")],
        }
        request = Request(scope)

        await middleware.dispatch(request, capture_context)

        assert captured_context is not None
        assert captured_context["request_id"] == "custom-id-123"

    async def test_middleware_adds_request_id_to_response(self) -> None:
        """Test middleware adds X-Request-ID to response headers."""

        async def return_ok(request: Request) -> Response:
            return Response(content="OK")

        middleware = RequestLoggingMiddleware(app=MagicMock())

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/",
            "query_string": b"",
            "headers": [],
        }
        request = Request(scope)

        response = await middleware.dispatch(request, return_ok)

        assert "X-Request-ID" in response.headers

    async def test_middleware_logs_request_start_and_end(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test middleware logs request lifecycle."""

        async def return_ok(request: Request) -> Response:
            return Response(content="OK", status_code=200)

        middleware = RequestLoggingMiddleware(app=MagicMock())

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/health",
            "query_string": b"",
            "headers": [],
        }
        request = Request(scope)

        with caplog.at_level(logging.INFO):
            await middleware.dispatch(request, return_ok)

        assert "Request started" in caplog.text
        assert "Request completed" in caplog.text

    async def test_middleware_logs_exception(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test middleware logs exceptions."""

        async def raise_error(request: Request) -> Response:
            raise ValueError("Something went wrong")

        middleware = RequestLoggingMiddleware(app=MagicMock())

        scope = {
            "type": "http",
            "method": "POST",
            "path": "/fail",
            "query_string": b"",
            "headers": [],
        }
        request = Request(scope)

        with caplog.at_level(logging.INFO), pytest.raises(ValueError):
            await middleware.dispatch(request, raise_error)

        assert "Request started" in caplog.text
        assert "Request failed" in caplog.text

    async def test_middleware_resets_context_after_request(self) -> None:
        """Test middleware resets context after request completes."""
        # Set some initial context
        initial_ctx = {"request_id": "initial"}
        token = request_context.set(initial_ctx)

        async def return_ok(request: Request) -> Response:
            return Response(content="OK")

        middleware = RequestLoggingMiddleware(app=MagicMock())

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/",
            "query_string": b"",
            "headers": [],
        }
        request = Request(scope)

        try:
            await middleware.dispatch(request, return_ok)
            # After middleware, context should be reset to initial
            assert request_context.get() == initial_ctx
        finally:
            request_context.reset(token)
