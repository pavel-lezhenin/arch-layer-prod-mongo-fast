"""Tests for main application module.

Uses testcontainers for isolated database instances.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from arch_layer_prod_mongo_fast.models.product import Product, ProductCreate
from arch_layer_prod_mongo_fast.repositories import MongoRepository


class TestLifespan:
    """Tests for application lifespan and Beanie initialization."""

    @pytest.mark.asyncio
    async def test_beanie_initialized_via_fixture(self, mongo_database: str) -> None:
        """Test that Beanie is properly initialized via conftest fixtures."""
        # The mongo_database fixture initializes Beanie with testcontainers
        # We verify Beanie works by performing an operation
        _ = mongo_database  # Used by fixture to initialize Beanie
        count = await Product.count()
        assert isinstance(count, int)
        assert count >= 0

    @pytest.mark.asyncio
    async def test_can_create_product_after_init(self, mongo_database: str) -> None:
        """Test that products can be created after Beanie initialization."""
        _ = mongo_database  # Used by fixture to initialize Beanie
        repo = MongoRepository()
        product_data = ProductCreate(
            name="Lifespan Test Product",
            description="Testing Beanie init",
            price=Decimal("10.00"),
            stock=1,
            category="Test",
        )

        product = await repo.create(product_data)
        assert product.name == "Lifespan Test Product"
        assert product.id is not None
