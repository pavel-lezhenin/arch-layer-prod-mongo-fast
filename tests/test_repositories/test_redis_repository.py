"""Tests for Redis repository."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest

from arch_layer_prod_mongo_fast.repositories.redis_repository import RedisRepository

if TYPE_CHECKING:
    from redis.asyncio import Redis


@pytest.fixture
def mock_redis() -> Redis:
    """Create a mock Redis client."""
    mock = MagicMock()
    mock.get = AsyncMock()
    mock.set = AsyncMock()
    mock.delete = AsyncMock()
    mock.exists = AsyncMock()
    mock.incr = AsyncMock()
    mock.flushdb = AsyncMock()
    mock.scan = AsyncMock()
    return mock


@pytest.fixture
def redis_repo(mock_redis: Redis) -> RedisRepository:
    """Create Redis repository with mock client."""
    return RedisRepository(mock_redis, ttl=300)


class TestRedisRepository:
    """Tests for Redis repository."""

    @pytest.mark.asyncio
    async def test_get_success(
        self,
        redis_repo: RedisRepository,
        mock_redis: Redis,
    ) -> None:
        """Test successful get operation."""
        mock_redis.get.return_value = '{"id": "123", "name": "Test"}'
        result = await redis_repo.get("test_key")
        assert result == {"id": "123", "name": "Test"}
        mock_redis.get.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_get_not_found(
        self,
        redis_repo: RedisRepository,
        mock_redis: Redis,
    ) -> None:
        """Test get when key not found."""
        mock_redis.get.return_value = None
        result = await redis_repo.get("missing_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_success(
        self,
        redis_repo: RedisRepository,
        mock_redis: Redis,
    ) -> None:
        """Test successful set operation."""
        data = {"id": "123", "name": "Test"}
        await redis_repo.set("test_key", data)
        mock_redis.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_success(
        self,
        redis_repo: RedisRepository,
        mock_redis: Redis,
    ) -> None:
        """Test successful delete operation."""
        await redis_repo.delete("test_key")
        mock_redis.delete.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_exists_true(
        self,
        redis_repo: RedisRepository,
        mock_redis: Redis,
    ) -> None:
        """Test exists returns True."""
        mock_redis.exists.return_value = 1
        result = await redis_repo.exists("test_key")
        assert result is True

    @pytest.mark.asyncio
    async def test_increment(
        self,
        redis_repo: RedisRepository,
        mock_redis: Redis,
    ) -> None:
        """Test increment operation."""
        mock_redis.incr.return_value = 5
        result = await redis_repo.increment("counter")
        assert result == 5
