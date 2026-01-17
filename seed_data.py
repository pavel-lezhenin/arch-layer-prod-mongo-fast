"""Script to seed demo data into MongoDB."""

from __future__ import annotations

import asyncio
from decimal import Decimal

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from arch_layer_prod_mongo_fast.config import get_settings
from arch_layer_prod_mongo_fast.models.product import Product, ProductCreate


async def seed_demo_data() -> None:
    """Seed database with demo product data."""
    settings = get_settings()

    client: AsyncIOMotorClient = AsyncIOMotorClient(settings.mongodb_uri)  # type: ignore[type-arg]
    database: AsyncIOMotorDatabase = client[settings.mongodb_database]  # type: ignore[type-arg]

    await init_beanie(database=database, document_models=[Product])  # type: ignore[arg-type]

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

    count = await Product.count()
    if count > 0:
        client.close()
        return

    for product_data in demo_products:
        product = Product(**product_data.model_dump())
        await product.insert()

    await Product.count()

    client.close()


if __name__ == "__main__":
    asyncio.run(seed_demo_data())
