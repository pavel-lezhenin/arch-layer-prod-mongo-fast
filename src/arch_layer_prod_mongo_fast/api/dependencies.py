"""Dependency injection for API layer."""

from __future__ import annotations

from typing import Annotated

from elasticsearch import AsyncElasticsearch
from fastapi import Depends
from redis.asyncio import Redis

from arch_layer_prod_mongo_fast.config import Settings, get_settings
from arch_layer_prod_mongo_fast.repositories import (
    ElasticRepository,
    MongoRepository,
    RedisRepository,
)
from arch_layer_prod_mongo_fast.services import ProductService


async def get_mongo_repo() -> MongoRepository:
    """Get MongoDB repository instance."""
    return MongoRepository()


async def get_redis_client(
    settings: Annotated[Settings, Depends(get_settings)],
) -> Redis:
    """Get Redis client instance."""
    client: Redis = Redis.from_url(
        settings.redis_uri,
        decode_responses=False,
    )
    return client


async def get_redis_repo(
    settings: Annotated[Settings, Depends(get_settings)],
    redis_client: Annotated[Redis, Depends(get_redis_client)],
) -> RedisRepository:
    """Get Redis repository instance."""
    return RedisRepository(redis_client, ttl=settings.redis_cache_ttl)


async def get_elastic_client(
    settings: Annotated[Settings, Depends(get_settings)],
) -> AsyncElasticsearch:
    """Get Elasticsearch client instance."""
    return AsyncElasticsearch([settings.elasticsearch_uri])


async def get_elastic_repo(
    settings: Annotated[Settings, Depends(get_settings)],
    es_client: Annotated[AsyncElasticsearch, Depends(get_elastic_client)],
) -> ElasticRepository:
    """Get Elasticsearch repository instance."""
    return ElasticRepository(es_client, settings.elasticsearch_index)


async def get_product_service(
    mongo_repo: Annotated[MongoRepository, Depends(get_mongo_repo)],
    redis_repo: Annotated[RedisRepository, Depends(get_redis_repo)],
    elastic_repo: Annotated[ElasticRepository, Depends(get_elastic_repo)],
) -> ProductService:
    """Get product service instance."""
    return ProductService(mongo_repo, redis_repo, elastic_repo)
