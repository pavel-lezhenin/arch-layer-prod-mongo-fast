"""Unit tests for RedisRepository error handling."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from arch_layer_prod_mongo_fast.exceptions import CacheError
from arch_layer_prod_mongo_fast.repositories.redis_repository import RedisRepository


@pytest.fixture
def mock_redis_client() -> MagicMock:
    """Create mock Redis client."""
    return MagicMock()


@pytest.fixture
def redis_repo(mock_redis_client: MagicMock) -> RedisRepository:
    """Create RedisRepository with mocked client."""
    return RedisRepository(mock_redis_client, ttl=3600)


class TestGetError:
    """Tests for get error handling."""

    async def test_get_raises_cache_error_on_failure(
        self,
        redis_repo: RedisRepository,
        mock_redis_client: MagicMock,
    ) -> None:
        """Should raise CacheError when get fails."""
        mock_redis_client.get = AsyncMock(side_effect=Exception("Get failed"))

        with pytest.raises(CacheError, match="Failed to get from cache"):
            await redis_repo.get("key")


class TestSetError:
    """Tests for set error handling."""

    async def test_set_raises_cache_error_on_failure(
        self,
        redis_repo: RedisRepository,
        mock_redis_client: MagicMock,
    ) -> None:
        """Should raise CacheError when set fails."""
        mock_redis_client.set = AsyncMock(side_effect=Exception("Set failed"))

        with pytest.raises(CacheError, match="Failed to set in cache"):
            await redis_repo.set("key", {"data": "value"})


class TestDeleteError:
    """Tests for delete error handling."""

    async def test_delete_raises_cache_error_on_failure(
        self,
        redis_repo: RedisRepository,
        mock_redis_client: MagicMock,
    ) -> None:
        """Should raise CacheError when delete fails."""
        mock_redis_client.delete = AsyncMock(side_effect=Exception("Delete failed"))

        with pytest.raises(CacheError, match="Failed to delete from cache"):
            await redis_repo.delete("key")


class TestDeletePatternError:
    """Tests for delete_pattern error handling."""

    async def test_delete_pattern_raises_cache_error_on_failure(
        self,
        redis_repo: RedisRepository,
        mock_redis_client: MagicMock,
    ) -> None:
        """Should raise CacheError when delete pattern fails."""
        mock_redis_client.scan = AsyncMock(side_effect=Exception("Scan failed"))

        with pytest.raises(CacheError, match="Failed to delete pattern"):
            await redis_repo.delete_pattern("products:*")


class TestExistsError:
    """Tests for exists error handling."""

    async def test_exists_raises_cache_error_on_failure(
        self,
        redis_repo: RedisRepository,
        mock_redis_client: MagicMock,
    ) -> None:
        """Should raise CacheError when exists check fails."""
        mock_redis_client.exists = AsyncMock(side_effect=Exception("Exists failed"))

        with pytest.raises(CacheError, match="Failed to check existence"):
            await redis_repo.exists("key")


class TestIncrementError:
    """Tests for increment error handling."""

    async def test_increment_raises_cache_error_on_failure(
        self,
        redis_repo: RedisRepository,
        mock_redis_client: MagicMock,
    ) -> None:
        """Should raise CacheError when increment fails."""
        mock_redis_client.incr = AsyncMock(side_effect=Exception("Incr failed"))

        with pytest.raises(CacheError, match="Failed to increment"):
            await redis_repo.increment("counter")


class TestClearAllError:
    """Tests for clear_all error handling."""

    async def test_clear_all_raises_cache_error_on_failure(
        self,
        redis_repo: RedisRepository,
        mock_redis_client: MagicMock,
    ) -> None:
        """Should raise CacheError when clear fails."""
        mock_redis_client.flushdb = AsyncMock(side_effect=Exception("Flush failed"))

        with pytest.raises(CacheError, match="Failed to clear cache"):
            await redis_repo.clear_all()
