"""Tests for API dependencies.

Uses testcontainers for isolated service instances.
"""

from __future__ import annotations

import pytest
from elasticsearch import AsyncElasticsearch
from redis.asyncio import Redis

from arch_layer_prod_mongo_fast.api.dependencies import (
    get_elastic_client,
    get_elastic_repo,
    get_mongo_repo,
    get_product_service,
    get_redis_client,
    get_redis_repo,
)
from arch_layer_prod_mongo_fast.config import Settings
from arch_layer_prod_mongo_fast.repositories import (
    ElasticRepository,
    MongoRepository,
    RedisRepository,
)
from arch_layer_prod_mongo_fast.services import ProductService


class TestMongoRepoDependency:
    """Tests for MongoDB repository dependency."""

    @pytest.mark.asyncio
    async def test_get_mongo_repo_returns_instance(
        self,
        mongo_database: str,
    ) -> None:
        """Test that get_mongo_repo returns MongoRepository instance."""
        repo = await get_mongo_repo()
        assert isinstance(repo, MongoRepository)


class TestRedisClientDependency:
    """Tests for Redis client dependency."""

    @pytest.mark.asyncio
    async def test_get_redis_client_returns_instance(
        self,
        redis_container,
    ) -> None:
        """Test that get_redis_client returns Redis instance."""
        host = redis_container.get_container_host_ip()
        port = redis_container.get_exposed_port(6379)
        settings = Settings(
            redis_uri=f"redis://{host}:{port}",
            _env_file=None,
        )
        client = await get_redis_client(settings)
        assert isinstance(client, Redis)
        await client.aclose()


class TestRedisRepoDependency:
    """Tests for Redis repository dependency."""

    @pytest.mark.asyncio
    async def test_get_redis_repo_returns_instance(
        self,
        redis_container,
    ) -> None:
        """Test that get_redis_repo returns RedisRepository instance."""
        host = redis_container.get_container_host_ip()
        port = redis_container.get_exposed_port(6379)
        settings = Settings(
            redis_uri=f"redis://{host}:{port}",
            redis_cache_ttl=600,
            _env_file=None,
        )
        redis_client = await get_redis_client(settings)
        repo = await get_redis_repo(settings, redis_client)
        assert isinstance(repo, RedisRepository)
        await redis_client.aclose()


class TestElasticClientDependency:
    """Tests for Elasticsearch client dependency."""

    @pytest.mark.asyncio
    async def test_get_elastic_client_returns_instance(
        self,
        elasticsearch_container,
    ) -> None:
        """Test that get_elastic_client returns AsyncElasticsearch instance."""
        host = elasticsearch_container.get_container_host_ip()
        port = elasticsearch_container.get_exposed_port(9200)
        url = f"http://{host}:{port}"
        settings = Settings(
            elasticsearch_uri=url,
            _env_file=None,
        )
        client = await get_elastic_client(settings)
        assert isinstance(client, AsyncElasticsearch)
        await client.close()


class TestElasticRepoDependency:
    """Tests for Elasticsearch repository dependency."""

    @pytest.mark.asyncio
    async def test_get_elastic_repo_returns_instance(
        self,
        elasticsearch_container,
    ) -> None:
        """Test that get_elastic_repo returns ElasticRepository instance."""
        host = elasticsearch_container.get_container_host_ip()
        port = elasticsearch_container.get_exposed_port(9200)
        url = f"http://{host}:{port}"
        settings = Settings(
            elasticsearch_uri=url,
            elasticsearch_index="test_products",
            _env_file=None,
        )
        es_client = await get_elastic_client(settings)
        repo = await get_elastic_repo(settings, es_client)
        assert isinstance(repo, ElasticRepository)
        await es_client.close()


class TestProductServiceDependency:
    """Tests for product service dependency."""

    @pytest.mark.asyncio
    async def test_get_product_service_returns_instance(
        self,
        mongo_repo: MongoRepository,
        redis_repo: RedisRepository,
        elastic_repo: ElasticRepository,
    ) -> None:
        """Test that get_product_service returns ProductService instance."""
        service = await get_product_service(mongo_repo, redis_repo, elastic_repo)
        assert isinstance(service, ProductService)
