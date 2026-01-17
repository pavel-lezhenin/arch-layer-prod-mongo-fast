"""Redis repository for caching operations."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from arch_layer_prod_mongo_fast.exceptions import CacheError

if TYPE_CHECKING:
    from redis.asyncio import Redis


class RedisRepository:
    """Repository for Redis cache operations."""

    def __init__(self, redis_client: Redis, ttl: int = 300) -> None:
        """Initialize Redis repository.

        Args:
            redis_client: Async Redis client instance
            ttl: Time-to-live in seconds (default: 5 minutes)
        """
        self._client = redis_client
        self._ttl = ttl

    async def get(self, key: str) -> dict[str, Any] | None:
        """Get value from cache."""
        try:
            value = await self._client.get(key)
            if value:
                result: dict[str, Any] = json.loads(value)
                return result
            return None  # noqa: TRY300
        except Exception as e:
            msg = f"Failed to get from cache: {e}"
            raise CacheError(msg) from e

    async def set(
        self,
        key: str,
        value: dict[str, Any],
        ttl: int | None = None,
    ) -> None:
        """Set value in cache with TTL."""
        try:
            serialized = json.dumps(value, default=str)
            await self._client.set(
                key,
                serialized,
                ex=ttl or self._ttl,
            )
        except Exception as e:
            msg = f"Failed to set in cache: {e}"
            raise CacheError(msg) from e

    async def delete(self, key: str) -> None:
        """Delete key from cache."""
        try:
            await self._client.delete(key)
        except Exception as e:
            msg = f"Failed to delete from cache: {e}"  # nosec B608  # noqa: S608
            raise CacheError(msg) from e

    async def delete_pattern(self, pattern: str) -> None:
        """Delete all keys matching pattern."""
        try:
            cursor = 0
            while True:
                cursor, keys = await self._client.scan(
                    cursor=cursor,
                    match=pattern,
                    count=100,
                )
                if keys:
                    await self._client.delete(*keys)
                if cursor == 0:
                    break
        except Exception as e:
            msg = f"Failed to delete pattern: {e}"
            raise CacheError(msg) from e

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            return bool(await self._client.exists(key))
        except Exception as e:
            msg = f"Failed to check existence: {e}"
            raise CacheError(msg) from e

    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment a counter."""
        try:
            result: int = await self._client.incr(key, amount)
            return result  # noqa: TRY300
        except Exception as e:
            msg = f"Failed to increment: {e}"
            raise CacheError(msg) from e

    async def clear_all(self) -> None:
        """Clear all keys (use with caution)."""
        try:
            await self._client.flushdb()
        except Exception as e:
            msg = f"Failed to clear cache: {e}"
            raise CacheError(msg) from e
