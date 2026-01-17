"""Custom exceptions for the application."""

from __future__ import annotations


class AppError(Exception):
    """Base exception for all application errors."""


class NotFoundError(AppError):
    """Raised when a resource is not found."""


class CacheError(AppError):
    """Raised when cache operations fail."""


class SearchError(AppError):
    """Raised when search operations fail."""


class DatabaseError(AppError):
    """Raised when database operations fail."""
