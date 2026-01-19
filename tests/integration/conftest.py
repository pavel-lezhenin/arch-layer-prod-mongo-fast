"""Pytest fixtures for integration tests using testcontainers.

Uses testcontainers to spin up isolated MongoDB, Redis, Elasticsearch
containers for each test session - ensuring tests don't affect real data.
"""

from __future__ import annotations

import contextlib
import time
from decimal import Decimal
from typing import TYPE_CHECKING

import pytest
from beanie import init_beanie
from elasticsearch import AsyncElasticsearch
from motor.motor_asyncio import AsyncIOMotorClient
from redis.asyncio import Redis
from testcontainers.core.container import DockerContainer
from testcontainers.core.wait_strategies import LogMessageWaitStrategy
from testcontainers.mongodb import MongoDbContainer
from testcontainers.redis import RedisContainer

from arch_layer_prod_mongo_fast.models.product import (
    Product,
    ProductCreate,
    ProductUpdate,
)
from arch_layer_prod_mongo_fast.repositories import (
    ElasticRepository,
    MongoRepository,
    RedisRepository,
)
from arch_layer_prod_mongo_fast.services import ProductService

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator


# =============================================================================
# TESTCONTAINERS FIXTURES (session-scoped for performance)
# =============================================================================


@pytest.fixture(scope="session")
def mongodb_container() -> Iterator[MongoDbContainer]:
    """Start MongoDB container for test session."""
    with MongoDbContainer("mongo:7.0") as mongo:
        yield mongo


@pytest.fixture(scope="session")
def redis_container() -> Iterator[RedisContainer]:
    """Start Redis container for test session."""
    with RedisContainer("redis:7-alpine") as redis:
        yield redis


@pytest.fixture(scope="session")
def elasticsearch_container() -> Iterator[DockerContainer]:
    """Start Elasticsearch 9.x container for test session.

    Note: testcontainers.elasticsearch doesn't support ES 9 yet,
    so we use DockerContainer directly.
    """
    container = (
        DockerContainer("docker.elastic.co/elasticsearch/elasticsearch:9.0.0")
        .with_exposed_ports(9200)
        .with_env("discovery.type", "single-node")
        .with_env("xpack.security.enabled", "false")
        .waiting_for(LogMessageWaitStrategy("started").with_startup_timeout(120))
    )
    with container:
        # Additional wait for HTTP to be fully available
        time.sleep(2)
        yield container


# =============================================================================
# CONNECTION FIXTURES
# =============================================================================


@pytest.fixture
async def mongo_client(
    mongodb_container: MongoDbContainer,
) -> AsyncIterator[AsyncIOMotorClient]:
    """Create async MongoDB client connected to test container."""
    connection_url = mongodb_container.get_connection_url()
    client: AsyncIOMotorClient = AsyncIOMotorClient(connection_url)  # type: ignore[type-arg]
    yield client
    client.close()


@pytest.fixture
async def mongo_database(
    mongo_client: AsyncIOMotorClient,
) -> AsyncIterator[str]:
    """Initialize Beanie with test database."""
    database_name = "test_db"
    database = mongo_client[database_name]
    await init_beanie(database=database, document_models=[Product])  # type: ignore[arg-type]
    yield database_name
    # Cleanup: drop all products after test
    await Product.delete_all()


@pytest.fixture
async def redis_client(
    redis_container: RedisContainer,
) -> AsyncIterator[Redis]:
    """Create async Redis client connected to test container."""
    host = redis_container.get_container_host_ip()
    port = redis_container.get_exposed_port(6379)
    client: Redis = Redis(host=host, port=int(port), decode_responses=False)
    yield client
    await client.flushdb()
    await client.aclose()


@pytest.fixture
async def elasticsearch_client(
    elasticsearch_container: DockerContainer,
) -> AsyncIterator[AsyncElasticsearch]:
    """Create async Elasticsearch client connected to test container."""
    host = elasticsearch_container.get_container_host_ip()
    port = elasticsearch_container.get_exposed_port(9200)
    url = f"http://{host}:{port}"
    client = AsyncElasticsearch([url])
    yield client
    # Cleanup - ignore errors during index deletion
    with contextlib.suppress(Exception):
        await client.indices.delete(index="products_test", ignore_unavailable=True)
    await client.close()


# =============================================================================
# REPOSITORY FIXTURES
# =============================================================================


@pytest.fixture
async def mongo_repo(mongo_database: str) -> MongoRepository:
    """Create MongoDB repository with initialized Beanie."""
    return MongoRepository()


@pytest.fixture
async def redis_repo(redis_client: Redis) -> RedisRepository:
    """Create Redis repository."""
    return RedisRepository(redis_client, ttl=300)


@pytest.fixture
async def elastic_repo(elasticsearch_client: AsyncElasticsearch) -> ElasticRepository:
    """Create Elasticsearch repository."""
    return ElasticRepository(elasticsearch_client, "products_test")


@pytest.fixture
async def product_service(
    mongo_repo: MongoRepository,
    redis_repo: RedisRepository,
    elastic_repo: ElasticRepository,
) -> ProductService:
    """Create product service with all repositories."""
    return ProductService(mongo_repo, redis_repo, elastic_repo)


# =============================================================================
# SAMPLE DATA FIXTURES
# =============================================================================


@pytest.fixture
def sample_product_create() -> ProductCreate:
    """Sample product creation data."""
    return ProductCreate(
        name="Test Product",
        description="This is a test product",
        price=Decimal("99.99"),
        stock=50,
        category="Test Category",
    )


@pytest.fixture
def sample_product_update() -> ProductUpdate:
    """Sample product update data."""
    return ProductUpdate(
        name="Updated Product",
        price=Decimal("149.99"),
        stock=75,
    )
