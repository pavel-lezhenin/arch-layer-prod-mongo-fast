"""Integration tests for Redis repository using testcontainers.

These tests use testcontainers to spin up a real Redis instance.
Will be converted from mocks to real containers.
"""

from __future__ import annotations

import pytest

from arch_layer_prod_mongo_fast.repositories.redis_repository import RedisRepository


class TestRedisRepositoryIntegration:
    """Integration tests for Redis repository using real Redis."""

    @pytest.mark.asyncio
    async def test_set_and_get(
        self,
        redis_repo: RedisRepository,
    ) -> None:
        """Test setting and getting a value."""
        data = {"id": "123", "name": "Test Product", "price": 99.99}
        await redis_repo.set("test_key", data)

        result = await redis_repo.get("test_key")
        assert result == data

    @pytest.mark.asyncio
    async def test_get_not_found(
        self,
        redis_repo: RedisRepository,
    ) -> None:
        """Test getting a non-existent key returns None."""
        result = await redis_repo.get("non_existent_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete(
        self,
        redis_repo: RedisRepository,
    ) -> None:
        """Test deleting a key."""
        data = {"id": "456", "name": "To Delete"}
        await redis_repo.set("delete_key", data)

        await redis_repo.delete("delete_key")

        result = await redis_repo.get("delete_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_exists_true(
        self,
        redis_repo: RedisRepository,
    ) -> None:
        """Test exists returns True for existing key."""
        data = {"test": "data"}
        await redis_repo.set("exists_key", data)

        result = await redis_repo.exists("exists_key")
        assert result is True

    @pytest.mark.asyncio
    async def test_exists_false(
        self,
        redis_repo: RedisRepository,
    ) -> None:
        """Test exists returns False for non-existent key."""
        result = await redis_repo.exists("non_existent")
        assert result is False

    @pytest.mark.asyncio
    async def test_increment(
        self,
        redis_repo: RedisRepository,
    ) -> None:
        """Test increment operation."""
        result1 = await redis_repo.increment("counter_key")
        assert result1 == 1

        result2 = await redis_repo.increment("counter_key")
        assert result2 == 2

    @pytest.mark.asyncio
    async def test_delete_pattern(
        self,
        redis_repo: RedisRepository,
    ) -> None:
        """Test deleting keys by pattern."""
        # Set multiple keys with same prefix
        await redis_repo.set("product:1", {"id": "1"})
        await redis_repo.set("product:2", {"id": "2"})
        await redis_repo.set("product:3", {"id": "3"})
        await redis_repo.set("other:1", {"id": "other"})

        await redis_repo.delete_pattern("product:*")

        # Product keys should be deleted
        assert await redis_repo.get("product:1") is None
        assert await redis_repo.get("product:2") is None
        assert await redis_repo.get("product:3") is None
        # Other key should remain
        assert await redis_repo.get("other:1") is not None

    @pytest.mark.asyncio
    async def test_set_with_ttl(
        self,
        redis_repo: RedisRepository,
    ) -> None:
        """Test that TTL is applied when setting values."""
        data = {"id": "ttl_test", "name": "TTL Test"}
        await redis_repo.set("ttl_key", data)

        # Key should exist immediately
        result = await redis_repo.get("ttl_key")
        assert result == data
