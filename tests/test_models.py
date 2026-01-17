"""Tests for product model."""

from __future__ import annotations

from decimal import Decimal

from arch_layer_prod_mongo_fast.models.product import (
    ProductCreate,
    ProductUpdate,
)


class TestProductCreate:
    """Tests for ProductCreate schema."""

    def test_valid_product_create(
        self,
        sample_product_create: ProductCreate,
    ) -> None:
        """Test creating a valid product."""
        assert sample_product_create.name == "Test Product"
        assert sample_product_create.price == Decimal("99.99")
        assert sample_product_create.stock == 50

    def test_product_create_defaults(self) -> None:
        """Test default values."""
        product = ProductCreate(
            name="Min Product",
            price=Decimal("10.00"),
            category="Test",
        )
        assert product.stock == 0
        assert product.is_active is True
        assert product.description is None


class TestProductUpdate:
    """Tests for ProductUpdate schema."""

    def test_valid_product_update(
        self,
        sample_product_update: ProductUpdate,
    ) -> None:
        """Test updating a product."""
        assert sample_product_update.name == "Updated Product"
        assert sample_product_update.price == Decimal("149.99")

    def test_product_update_partial(self) -> None:
        """Test partial update."""
        update = ProductUpdate(name="New Name")
        assert update.name == "New Name"
        assert update.price is None
        assert update.stock is None
