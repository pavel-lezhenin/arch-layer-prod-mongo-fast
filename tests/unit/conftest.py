"""Pytest fixtures for unit tests.

Unit tests use mocks, no testcontainers needed.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from arch_layer_prod_mongo_fast.models.product import (
    ProductCreate,
    ProductUpdate,
)

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


@pytest.fixture
def mock_products_list() -> list[dict]:
    """Mock list of products for testing."""
    return [
        {
            "id": "507f1f77bcf86cd799439011",
            "name": "Mock Product 1",
            "description": "First mock product",
            "price": 29.99,
            "stock": 100,
            "category": "Category A",
            "is_active": True,
        },
        {
            "id": "507f1f77bcf86cd799439012",
            "name": "Mock Product 2",
            "description": "Second mock product",
            "price": 59.99,
            "stock": 50,
            "category": "Category B",
            "is_active": True,
        },
        {
            "id": "507f1f77bcf86cd799439013",
            "name": "Mock Product 3",
            "description": "Third mock product",
            "price": 19.99,
            "stock": 200,
            "category": "Category A",
            "is_active": False,
        },
    ]
