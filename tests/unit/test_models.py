"""Unit tests for product model."""

from __future__ import annotations

from decimal import Decimal
from unittest.mock import MagicMock

from bson import Decimal128

from arch_layer_prod_mongo_fast.models.product import (
    Product,
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


class TestProductValidators:
    """Tests for Product validators and serializers."""

    def test_convert_decimal128_with_decimal128(self) -> None:
        """Test converting Decimal128 to Decimal."""
        decimal128_value = Decimal128(Decimal("99.99"))
        result = Product.convert_decimal128(decimal128_value)
        assert isinstance(result, Decimal)
        assert result == Decimal("99.99")

    def test_convert_decimal128_with_decimal(self) -> None:
        """Test converting Decimal returns same Decimal."""
        decimal_value = Decimal("99.99")
        result = Product.convert_decimal128(decimal_value)
        assert result is decimal_value

    def test_convert_decimal128_with_string(self) -> None:
        """Test converting string to Decimal."""
        result = Product.convert_decimal128("99.99")
        assert isinstance(result, Decimal)
        assert result == Decimal("99.99")

    def test_convert_decimal128_with_float(self) -> None:
        """Test converting float to Decimal."""
        result = Product.convert_decimal128(99.99)
        assert isinstance(result, Decimal)

    def test_serialize_id_with_none(self) -> None:
        """Test serializing None id returns None."""
        result = Product.serialize_id(None)
        assert result is None

    def test_serialize_id_with_object_id(self) -> None:
        """Test serializing ObjectId to string."""
        mock_id = MagicMock()
        mock_id.__str__ = MagicMock(return_value="507f1f77bcf86cd799439011")
        result = Product.serialize_id(mock_id)
        assert result == "507f1f77bcf86cd799439011"
