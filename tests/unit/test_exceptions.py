"""Tests for custom exceptions."""

from __future__ import annotations

import pytest

from arch_layer_prod_mongo_fast.exceptions import (
    AppError,
    CacheError,
    DatabaseError,
    NotFoundError,
    SearchError,
)


class TestAppError:
    """Tests for AppError base exception."""

    def test_app_error_is_exception(self) -> None:
        """Test that AppError inherits from Exception."""
        error = AppError("Test error")
        assert isinstance(error, Exception)

    def test_app_error_message(self) -> None:
        """Test that AppError stores message."""
        error = AppError("Test message")
        assert str(error) == "Test message"

    def test_app_error_can_be_raised(self) -> None:
        """Test that AppError can be raised and caught."""
        with pytest.raises(AppError) as exc_info:
            raise AppError("Raised error")
        assert "Raised error" in str(exc_info.value)


class TestNotFoundError:
    """Tests for NotFoundError exception."""

    def test_not_found_error_inherits_from_app_error(self) -> None:
        """Test that NotFoundError inherits from AppError."""
        error = NotFoundError("Not found")
        assert isinstance(error, AppError)
        assert isinstance(error, Exception)

    def test_not_found_error_message(self) -> None:
        """Test that NotFoundError stores message."""
        error = NotFoundError("Resource not found")
        assert str(error) == "Resource not found"

    def test_not_found_error_can_be_raised(self) -> None:
        """Test that NotFoundError can be raised and caught."""
        with pytest.raises(NotFoundError):
            raise NotFoundError("Product not found")


class TestCacheError:
    """Tests for CacheError exception."""

    def test_cache_error_inherits_from_app_error(self) -> None:
        """Test that CacheError inherits from AppError."""
        error = CacheError("Cache error")
        assert isinstance(error, AppError)

    def test_cache_error_can_be_raised(self) -> None:
        """Test that CacheError can be raised and caught."""
        with pytest.raises(CacheError):
            raise CacheError("Redis connection failed")


class TestSearchError:
    """Tests for SearchError exception."""

    def test_search_error_inherits_from_app_error(self) -> None:
        """Test that SearchError inherits from AppError."""
        error = SearchError("Search error")
        assert isinstance(error, AppError)

    def test_search_error_can_be_raised(self) -> None:
        """Test that SearchError can be raised and caught."""
        with pytest.raises(SearchError):
            raise SearchError("Elasticsearch unavailable")


class TestDatabaseError:
    """Tests for DatabaseError exception."""

    def test_database_error_inherits_from_app_error(self) -> None:
        """Test that DatabaseError inherits from AppError."""
        error = DatabaseError("DB error")
        assert isinstance(error, AppError)

    def test_database_error_can_be_raised(self) -> None:
        """Test that DatabaseError can be raised and caught."""
        with pytest.raises(DatabaseError):
            raise DatabaseError("MongoDB connection failed")


class TestExceptionHierarchy:
    """Tests for exception hierarchy."""

    def test_all_errors_catchable_as_app_error(self) -> None:
        """Test that all custom errors can be caught as AppError."""
        errors = [
            NotFoundError("test"),
            CacheError("test"),
            SearchError("test"),
            DatabaseError("test"),
        ]

        for error in errors:
            with pytest.raises(AppError):
                raise error
