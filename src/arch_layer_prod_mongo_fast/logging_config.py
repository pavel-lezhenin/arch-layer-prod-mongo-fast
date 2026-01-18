"""Logging configuration with structured JSON output."""

from __future__ import annotations

import json
import logging
import sys
from contextvars import ContextVar
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Context variable for request-scoped data (request_id, user, etc.)
request_context: ContextVar[dict[str, Any] | None] = ContextVar(
    "request_context",
    default=None,
)


class ContextFilter(logging.Filter):
    """Filter that adds context variables to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Add request context to log record."""
        ctx = request_context.get() or {}
        record.request_id = ctx.get("request_id", "-")
        record.path = ctx.get("path", "-")
        record.method = ctx.get("method", "-")
        return True


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
            "path": getattr(record, "path", "-"),
            "method": getattr(record, "method", "-"),
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        extra_keys = set(record.__dict__) - {
            "name",
            "msg",
            "args",
            "created",
            "filename",
            "funcName",
            "levelname",
            "levelno",
            "lineno",
            "module",
            "msecs",
            "pathname",
            "process",
            "processName",
            "relativeCreated",
            "stack_info",
            "exc_info",
            "exc_text",
            "thread",
            "threadName",
            "request_id",
            "path",
            "method",
            "message",
            "taskName",
        }
        for key in extra_keys:
            log_data[key] = getattr(record, key)

        return json.dumps(log_data, default=str)


def setup_logging(
    level: str = "INFO",
    json_format: bool = True,
    log_file: str | None = None,
) -> None:
    """Configure logging for the application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        json_format: Use JSON format (True for production, False for development)
        log_file: Optional file path for JSON logs (for Loki/Promtail)
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    if json_format:
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(request_id)s | "
                "%(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

    console_handler.addFilter(ContextFilter())
    root_logger.addHandler(console_handler)

    # File handler for Loki/Promtail (always JSON)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(JSONFormatter())
        file_handler.addFilter(ContextFilter())
        root_logger.addHandler(file_handler)

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("motor").setLevel(logging.WARNING)
    logging.getLogger("elasticsearch").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the package namespace.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(f"arch_layer_prod_mongo_fast.{name}")
