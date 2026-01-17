"""Script to seed demo data into MongoDB and Elasticsearch."""

from __future__ import annotations

import asyncio
import logging
from decimal import Decimal

from beanie import init_beanie
from elasticsearch import AsyncElasticsearch
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from redis.asyncio import Redis

from arch_layer_prod_mongo_fast.config import get_settings
from arch_layer_prod_mongo_fast.models.product import Product, ProductCreate
from arch_layer_prod_mongo_fast.repositories.elastic_repository import (
    ElasticRepository,
)
from arch_layer_prod_mongo_fast.repositories.mongo_repository import MongoRepository
from arch_layer_prod_mongo_fast.repositories.redis_repository import RedisRepository
from arch_layer_prod_mongo_fast.services.product_service import ProductService


async def seed_demo_data() -> None:
    """Seed database with demo product data."""
    settings = get_settings()

    # Initialize MongoDB
    client: AsyncIOMotorClient = AsyncIOMotorClient(settings.mongodb_uri)  # type: ignore[type-arg]
    database: AsyncIOMotorDatabase = client[settings.mongodb_database]  # type: ignore[type-arg]
    await init_beanie(database=database, document_models=[Product])  # type: ignore[arg-type]

    # Initialize Redis and Elasticsearch
    redis_client = Redis.from_url(settings.redis_uri, decode_responses=True)
    es_client = AsyncElasticsearch([settings.elasticsearch_uri])

    # Create repositories
    mongo_repo = MongoRepository()
    redis_repo = RedisRepository(redis_client)
    elastic_repo = ElasticRepository(es_client, "products")

    # Create service
    product_service = ProductService(mongo_repo, redis_repo, elastic_repo)

    demo_products = [
        ProductCreate(
            name="Laptop Pro 15",
            description="High-performance laptop with 16GB RAM and 512GB SSD",
            price=Decimal("1299.99"),
            stock=25,
            category="Electronics",
        ),
        ProductCreate(
            name="Wireless Mouse",
            description="Ergonomic wireless mouse with USB receiver",
            price=Decimal("29.99"),
            stock=150,
            category="Electronics",
        ),
        ProductCreate(
            name="Office Chair",
            description="Ergonomic office chair with lumbar support",
            price=Decimal("249.50"),
            stock=40,
            category="Furniture",
        ),
        ProductCreate(
            name="Standing Desk",
            description="Adjustable height standing desk, electric motor",
            price=Decimal("599.00"),
            stock=15,
            category="Furniture",
        ),
        ProductCreate(
            name="Python Programming Book",
            description="Comprehensive guide to Python 3.11+",
            price=Decimal("49.99"),
            stock=200,
            category="Books",
        ),
        ProductCreate(
            name="Mechanical Keyboard",
            description="RGB mechanical keyboard with Cherry MX switches",
            price=Decimal("159.99"),
            stock=80,
            category="Electronics",
        ),
        ProductCreate(
            name="USB-C Hub",
            description="7-in-1 USB-C hub with HDMI, USB 3.0, SD card reader",
            price=Decimal("39.99"),
            stock=120,
            category="Electronics",
        ),
        ProductCreate(
            name="Monitor 27 inch 4K",
            description="4K UHD monitor with HDR support",
            price=Decimal("449.00"),
            stock=30,
            category="Electronics",
        ),
        ProductCreate(
            name="Desk Lamp LED",
            description="Adjustable LED desk lamp with touch controls",
            price=Decimal("34.99"),
            stock=95,
            category="Furniture",
        ),
        ProductCreate(
            name="Noise-Cancelling Headphones",
            description="Premium over-ear headphones with active noise cancellation",
            price=Decimal("299.99"),
            stock=60,
            category="Electronics",
        ),
        ProductCreate(
            name="Webcam 1080p",
            description="Full HD webcam with auto-focus and dual microphones",
            price=Decimal("79.99"),
            stock=110,
            category="Electronics",
            is_active=False,
        ),
        ProductCreate(
            name="Desk Organizer",
            description="Bamboo desk organizer with multiple compartments",
            price=Decimal("24.99"),
            stock=200,
            category="Furniture",
        ),
    ]

    logger = logging.getLogger(__name__)
    count = await Product.count()
    if count > 0:
        logger.info("Database already contains %d products. Skipping seed.", count)
        await es_client.close()
        await redis_client.aclose()
        client.close()
        return

    logger.info("Seeding %d products...", len(demo_products))
    for i, product_data in enumerate(demo_products, 1):
        await product_service.create(product_data)
        logger.info("  [%d/%d] Created: %s", i, len(demo_products), product_data.name)

    total = await Product.count()
    logger.info("Successfully seeded %d products into MongoDB and Elasticsearch", total)

    await es_client.close()
    await redis_client.aclose()
    client.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    asyncio.run(seed_demo_data())
