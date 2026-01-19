"""Tests for logging configuration and utilities."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

import pytest

from arch_layer_prod_mongo_fast.logging_config import (
    ContextFilter,
    JSONFormatter,
    get_logger,
    request_context,
    setup_logging,
)
from arch_layer_prod_mongo_fast.utils.logging_decorators import (
    log_operation,
    log_operation_sync,
)

if TYPE_CHECKING:
    from pathlib import Path


class TestJSONFormatter:
    """Test JSONFormatter."""

    def test_format_basic_record(self) -> None:
        """Test formatting a basic log record."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.request_id = "req-123"
        record.path = "/api/test"
        record.method = "GET"

        result = formatter.format(record)
        data = json.loads(result)

        assert data["level"] == "INFO"
        assert data["logger"] == "test"
        assert data["message"] == "Test message"
        assert data["request_id"] == "req-123"
        assert data["path"] == "/api/test"
        assert data["method"] == "GET"
        assert "timestamp" in data

    def test_format_with_exception(self) -> None:
        """Test formatting a log record with exception."""
        import sys

        formatter = JSONFormatter()

        try:
            msg = "Test error"
            raise ValueError(msg)
        except ValueError:
            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=10,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )
        record.request_id = "-"
        record.path = "-"
        record.method = "-"

        result = formatter.format(record)
        data = json.loads(result)

        assert data["level"] == "ERROR"
        assert "exception" in data
        assert "ValueError" in data["exception"]

    def test_format_with_extra_fields(self) -> None:
        """Test formatting with extra fields."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test",
            args=(),
            exc_info=None,
        )
        record.request_id = "-"
        record.path = "-"
        record.method = "-"
        record.duration_ms = 42.5
        record.custom_field = "custom_value"

        result = formatter.format(record)
        data = json.loads(result)

        assert data["duration_ms"] == 42.5
        assert data["custom_field"] == "custom_value"


class TestContextFilter:
    """Test ContextFilter."""

    def test_filter_adds_context(self) -> None:
        """Test filter adds request context to record."""
        ctx = {"request_id": "ctx-123", "path": "/test", "method": "POST"}
        token = request_context.set(ctx)

        try:
            filter_ = ContextFilter()
            record = logging.LogRecord(
                name="test",
                level=logging.INFO,
                pathname="test.py",
                lineno=10,
                msg="Test",
                args=(),
                exc_info=None,
            )

            result = filter_.filter(record)

            assert result is True
            assert record.request_id == "ctx-123"
            assert record.path == "/test"
            assert record.method == "POST"
        finally:
            request_context.reset(token)

    def test_filter_without_context(self) -> None:
        """Test filter works when no context is set."""
        filter_ = ContextFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test",
            args=(),
            exc_info=None,
        )

        result = filter_.filter(record)

        assert result is True
        assert record.request_id == "-"
        assert record.path == "-"
        assert record.method == "-"


class TestSetupLogging:
    """Test setup_logging function."""

    def test_setup_logging_json_format(self) -> None:
        """Test logging setup with JSON format."""
        setup_logging(level="DEBUG", json_format=True)

        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG
        assert len(root_logger.handlers) >= 1

        # Check handler has JSON formatter
        handler = root_logger.handlers[0]
        assert isinstance(handler.formatter, JSONFormatter)

    def test_setup_logging_text_format(self) -> None:
        """Test logging setup with text format."""
        setup_logging(level="INFO", json_format=False)

        root_logger = logging.getLogger()
        assert root_logger.level == logging.INFO

        # Check handler has regular formatter
        handler = root_logger.handlers[0]
        assert not isinstance(handler.formatter, JSONFormatter)

    def test_setup_logging_with_file(self, tmp_path: Path) -> None:
        """Test logging setup with file output."""
        log_file = tmp_path / "logs" / "test.log"
        setup_logging(level="INFO", json_format=True, log_file=str(log_file))

        root_logger = logging.getLogger()
        # Should have console + file handlers
        assert len(root_logger.handlers) >= 2


class TestGetLogger:
    """Test get_logger function."""

    def test_get_logger_returns_namespaced_logger(self) -> None:
        """Test get_logger returns properly namespaced logger."""
        logger = get_logger("test_module")

        assert logger.name == "arch_layer_prod_mongo_fast.test_module"


class TestLogOperationDecorator:
    """Test log_operation decorator."""

    async def test_log_operation_success(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test decorator logs successful operation."""

        @log_operation("Test operation")
        async def sample_func() -> str:
            return "result"

        with caplog.at_level(logging.DEBUG):
            result = await sample_func()

        assert result == "result"
        assert "Test operation started" in caplog.text
        assert "Test operation completed" in caplog.text

    async def test_log_operation_failure(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test decorator logs failed operation."""

        @log_operation("Failing operation")
        async def failing_func() -> None:
            raise ValueError("Test error")

        with (
            caplog.at_level(logging.DEBUG),
            pytest.raises(ValueError, match="Test error"),
        ):
            await failing_func()

        assert "Failing operation started" in caplog.text
        assert "Failing operation failed" in caplog.text

    async def test_log_operation_with_args(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test decorator can log arguments."""

        @log_operation("With args", log_args=True)
        async def func_with_args(*, name: str, count: int) -> str:
            return f"{name}:{count}"

        with caplog.at_level(logging.DEBUG):
            result = await func_with_args(name="test", count=5)

        assert result == "test:5"

    async def test_log_operation_filters_sensitive_args(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test decorator filters sensitive arguments."""

        @log_operation("Sensitive", log_args=True)
        async def func_with_password(*, username: str, password: str) -> str:
            return username

        with caplog.at_level(logging.DEBUG):
            await func_with_password(username="user", password="secret123")

        # Password should not appear in logs
        assert "secret123" not in caplog.text


class TestLogOperationSyncDecorator:
    """Test log_operation_sync decorator."""

    def test_log_operation_sync_success(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test sync decorator logs successful operation."""

        @log_operation_sync("Sync operation")
        def sync_func() -> int:
            return 42

        with caplog.at_level(logging.DEBUG):
            result = sync_func()

        assert result == 42
        assert "Sync operation started" in caplog.text
        assert "Sync operation completed" in caplog.text

    def test_log_operation_sync_failure(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test sync decorator logs failed operation."""

        @log_operation_sync("Sync failing")
        def sync_failing() -> None:
            raise RuntimeError("Sync error")

        with (
            caplog.at_level(logging.DEBUG),
            pytest.raises(RuntimeError, match="Sync error"),
        ):
            sync_failing()

        assert "Sync failing started" in caplog.text
        assert "Sync failing failed" in caplog.text
