"""API route unit tests with mocked service.

Uses mock ProductService to test API routes in isolation.
No testcontainers needed - pure unit tests for HTTP layer.
Uses a test app without lifespan to avoid MongoDB connections.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from arch_layer_prod_mongo_fast.api.dependencies import get_product_service
from arch_layer_prod_mongo_fast.api.routes import router
from arch_layer_prod_mongo_fast.exceptions import NotFoundError

if TYPE_CHECKING:
    from collections.abc import Generator


def create_test_app() -> FastAPI:
    """Create a test FastAPI app without lifespan (no MongoDB connection)."""
    test_app = FastAPI(title="Test App")
    test_app.include_router(router)

    @test_app.get("/", tags=["health"])
    async def root() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "ok", "message": "Layered Architecture API"}

    return test_app


def create_mock_product(
    product_id: str = "507f1f77bcf86cd799439011",
    name: str = "Test Product",
    description: str = "Test description",
    price: Decimal = Decimal("99.99"),
    stock: int = 50,
    category: str = "Test Category",
    is_active: bool = True,
) -> MagicMock:
    """Create a mock product with model_dump method."""
    now = datetime.now(UTC)
    product = MagicMock()
    product.model_dump.return_value = {
        "id": product_id,
        "name": name,
        "description": description,
        "price": price,
        "stock": stock,
        "category": category,
        "is_active": is_active,
        "created_at": now,
        "updated_at": now,
    }
    return product


@pytest.fixture
def mock_service() -> MagicMock:
    """Create mock ProductService."""
    service = MagicMock()
    service.create = AsyncMock()
    service.get_by_id = AsyncMock()
    service.update = AsyncMock()
    service.delete = AsyncMock()
    service.list_all = AsyncMock()
    service.search = AsyncMock()
    service.search_by_category = AsyncMock()
    service.search_by_price_range = AsyncMock()
    service.reindex_all = AsyncMock()
    service.clear_cache = AsyncMock()
    service.count = AsyncMock()
    return service


@pytest.fixture
def test_client(mock_service: MagicMock) -> Generator[TestClient]:
    """Create test client with mocked service and no lifespan."""
    app = create_test_app()

    async def override_get_product_service() -> MagicMock:
        return mock_service

    app.dependency_overrides[get_product_service] = override_get_product_service

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


class TestProductCRUD:
    """Tests for product CRUD operations."""

    def test_create_product(
        self,
        test_client: TestClient,
        mock_service: MagicMock,
    ) -> None:
        """Test creating a new product."""
        mock_product = create_mock_product()
        mock_service.create.return_value = mock_product

        product_data = {
            "name": "Test Product",
            "description": "Test description",
            "price": "99.99",
            "stock": 50,
            "category": "Test Category",
        }
        response = test_client.post("/api/v1/products/", json=product_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Product"
        assert data["description"] == "Test description"
        assert Decimal(str(data["price"])) == Decimal("99.99")
        assert data["stock"] == 50
        assert data["category"] == "Test Category"
        assert data["is_active"] is True
        mock_service.create.assert_called_once()

    def test_get_product(
        self,
        test_client: TestClient,
        mock_service: MagicMock,
    ) -> None:
        """Test getting a product by ID."""
        product_id = "507f1f77bcf86cd799439011"
        mock_product = create_mock_product(product_id=product_id)
        mock_service.get_by_id.return_value = mock_product

        response = test_client.get(f"/api/v1/products/{product_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == product_id
        assert data["name"] == "Test Product"
        mock_service.get_by_id.assert_called_once_with(product_id)

    def test_get_product_not_found(
        self,
        test_client: TestClient,
        mock_service: MagicMock,
    ) -> None:
        """Test getting a non-existent product."""
        product_id = "507f1f77bcf86cd799439099"
        error_msg = f"Product {product_id} not found"
        mock_service.get_by_id.side_effect = NotFoundError(error_msg)

        response = test_client.get(f"/api/v1/products/{product_id}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_update_product(
        self,
        test_client: TestClient,
        mock_service: MagicMock,
    ) -> None:
        """Test updating a product."""
        product_id = "507f1f77bcf86cd799439011"
        mock_product = create_mock_product(
            product_id=product_id,
            name="Updated Product",
            price=Decimal("149.99"),
        )
        mock_service.update.return_value = mock_product

        update_data = {"name": "Updated Product", "price": "149.99"}
        response = test_client.put(f"/api/v1/products/{product_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Product"
        assert Decimal(str(data["price"])) == Decimal("149.99")
        mock_service.update.assert_called_once()

    def test_update_product_not_found(
        self,
        test_client: TestClient,
        mock_service: MagicMock,
    ) -> None:
        """Test updating a non-existent product."""
        product_id = "507f1f77bcf86cd799439099"
        error_msg = f"Product {product_id} not found"
        mock_service.update.side_effect = NotFoundError(error_msg)

        response = test_client.put(
            f"/api/v1/products/{product_id}",
            json={"name": "Updated"},
        )

        assert response.status_code == 404

    def test_delete_product(
        self,
        test_client: TestClient,
        mock_service: MagicMock,
    ) -> None:
        """Test deleting a product."""
        product_id = "507f1f77bcf86cd799439011"
        mock_service.delete.return_value = None

        response = test_client.delete(f"/api/v1/products/{product_id}")

        assert response.status_code == 204
        mock_service.delete.assert_called_once_with(product_id)

    def test_delete_product_not_found(
        self,
        test_client: TestClient,
        mock_service: MagicMock,
    ) -> None:
        """Test deleting a non-existent product."""
        product_id = "507f1f77bcf86cd799439099"
        error_msg = f"Product {product_id} not found"
        mock_service.delete.side_effect = NotFoundError(error_msg)

        response = test_client.delete(f"/api/v1/products/{product_id}")

        assert response.status_code == 404

    def test_list_products(
        self,
        test_client: TestClient,
        mock_service: MagicMock,
    ) -> None:
        """Test listing products."""
        mock_products = [
            create_mock_product(product_id=f"id{i}", name=f"Product {i}")
            for i in range(3)
        ]
        mock_service.list_all.return_value = mock_products

        response = test_client.get("/api/v1/products/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        mock_service.list_all.assert_called_once()

    def test_list_products_with_pagination(
        self,
        test_client: TestClient,
        mock_service: MagicMock,
    ) -> None:
        """Test listing products with pagination."""
        mock_service.list_all.return_value = []

        response = test_client.get("/api/v1/products/?skip=10&limit=5")

        assert response.status_code == 200
        mock_service.list_all.assert_called_once_with(
            skip=10,
            limit=5,
            category=None,
            is_active=None,
        )

    def test_list_products_filter_by_category(
        self,
        test_client: TestClient,
        mock_service: MagicMock,
    ) -> None:
        """Test listing products filtered by category."""
        mock_service.list_all.return_value = []

        response = test_client.get("/api/v1/products/?category=Electronics")

        assert response.status_code == 200
        mock_service.list_all.assert_called_once_with(
            skip=0,
            limit=100,
            category="Electronics",
            is_active=None,
        )

    def test_list_products_filter_by_is_active(
        self,
        test_client: TestClient,
        mock_service: MagicMock,
    ) -> None:
        """Test listing products filtered by is_active."""
        mock_service.list_all.return_value = []

        response = test_client.get("/api/v1/products/?is_active=true")

        assert response.status_code == 200
        mock_service.list_all.assert_called_once_with(
            skip=0,
            limit=100,
            category=None,
            is_active=True,
        )


class TestSearchEndpoints:
    """Tests for search endpoints."""

    def test_search_products(
        self,
        test_client: TestClient,
        mock_service: MagicMock,
    ) -> None:
        """Test full-text search."""
        now = datetime.now(UTC)
        mock_service.search.return_value = [
            {
                "id": "id1",
                "name": "Test",
                "description": "Desc",
                "price": Decimal("10.00"),
                "stock": 10,
                "category": "Cat",
                "is_active": True,
                "created_at": now,
                "updated_at": now,
            },
        ]

        response = test_client.get("/api/v1/products/search/text?q=test")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        mock_service.search.assert_called_once_with("test", 10)

    def test_search_by_category(
        self,
        test_client: TestClient,
        mock_service: MagicMock,
    ) -> None:
        """Test search by category."""
        now = datetime.now(UTC)
        mock_service.search_by_category.return_value = [
            {
                "id": "id1",
                "name": "Test",
                "description": "Desc",
                "price": Decimal("10.00"),
                "stock": 10,
                "category": "Electronics",
                "is_active": True,
                "created_at": now,
                "updated_at": now,
            },
        ]

        response = test_client.get("/api/v1/products/search/category/Electronics")

        assert response.status_code == 200
        mock_service.search_by_category.assert_called_once_with("Electronics")

    def test_search_by_price_range(
        self,
        test_client: TestClient,
        mock_service: MagicMock,
    ) -> None:
        """Test search by price range."""
        mock_service.search_by_price_range.return_value = []

        response = test_client.get(
            "/api/v1/products/search/price?min_price=10&max_price=100"
        )

        assert response.status_code == 200
        mock_service.search_by_price_range.assert_called_once_with(10.0, 100.0)


class TestCacheEndpoints:
    """Tests for cache endpoints."""

    def test_clear_cache(
        self,
        test_client: TestClient,
        mock_service: MagicMock,
    ) -> None:
        """Test clearing cache."""
        mock_service.clear_cache.return_value = None

        response = test_client.delete("/api/v1/products/cache")

        assert response.status_code == 204
        mock_service.clear_cache.assert_called_once()


class TestReindexEndpoint:
    """Tests for reindex endpoint."""

    def test_reindex_products(
        self,
        test_client: TestClient,
        mock_service: MagicMock,
    ) -> None:
        """Test reindexing products."""
        mock_service.reindex_all.return_value = 42

        response = test_client.post("/api/v1/products/reindex")

        assert response.status_code == 200
        data = response.json()
        assert data["indexed"] == 42
        mock_service.reindex_all.assert_called_once()


class TestCountEndpoint:
    """Tests for count endpoint."""

    def test_get_product_count(
        self,
        test_client: TestClient,
        mock_service: MagicMock,
    ) -> None:
        """Test getting product count."""
        mock_service.count.return_value = 100

        response = test_client.get("/api/v1/products/stats/count")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 100
        mock_service.count.assert_called_once()


class TestHealthEndpoint:
    """Tests for health endpoint."""

    def test_root_health(self, test_client: TestClient) -> None:
        """Test root health check endpoint."""
        response = test_client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
