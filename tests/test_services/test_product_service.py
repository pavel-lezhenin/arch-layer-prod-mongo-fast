"""Tests for product service."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from arch_layer_prod_mongo_fast.exceptions import CacheError, SearchError
from arch_layer_prod_mongo_fast.models.product import (
    Product,
    ProductCreate,
    ProductUpdate,
)
from arch_layer_prod_mongo_fast.services.product_service import ProductService

if TYPE_CHECKING:
    from arch_layer_prod_mongo_fast.repositories.elastic_repository import (
        ElasticRepository,
    )
    from arch_layer_prod_mongo_fast.repositories.mongo_repository import (
        MongoRepository,
    )
    from arch_layer_prod_mongo_fast.repositories.redis_repository import (
        RedisRepository,
    )


@pytest.fixture
def mock_mongo_repo() -> MongoRepository:
    """Create mock MongoDB repository."""
    mock = MagicMock()
    mock.create = AsyncMock()
    mock.get_by_id = AsyncMock()
    mock.update = AsyncMock()
    mock.delete = AsyncMock()
    mock.list_all = AsyncMock()
    mock.count = AsyncMock()
    return mock


@pytest.fixture
def mock_redis_repo() -> RedisRepository:
    """Create mock Redis repository."""
    mock = MagicMock()
    mock.get = AsyncMock()
    mock.set = AsyncMock()
    mock.delete = AsyncMock()
    mock.delete_pattern = AsyncMock()
    return mock


@pytest.fixture
def mock_elastic_repo() -> ElasticRepository:
    """Create mock Elasticsearch repository."""
    mock = MagicMock()
    mock.index_document = AsyncMock()
    mock.delete_document = AsyncMock()
    mock.search = AsyncMock()
    mock.search_by_category = AsyncMock()
    mock.search_by_price_range = AsyncMock()
    mock.bulk_index = AsyncMock()
    return mock


@pytest.fixture
def mock_product_service(
    mock_mongo_repo: MongoRepository,
    mock_redis_repo: RedisRepository,
    mock_elastic_repo: ElasticRepository,
) -> ProductService:
    """Create product service with mock repositories."""
    return ProductService(mock_mongo_repo, mock_redis_repo, mock_elastic_repo)


class TestProductServiceCreate:
    """Tests for product creation."""

    @pytest.mark.asyncio
    async def test_create_product(
        self,
        mock_product_service: ProductService,
        mock_mongo_repo: MongoRepository,
        mock_elastic_repo: ElasticRepository,
        sample_product_create: ProductCreate,
    ) -> None:
        """Test product creation indexes in Elasticsearch."""
        mock_product = MagicMock(spec=Product)
        mock_product.id = "123"
        mock_product.model_dump.return_value = {"id": "123", "name": "Test"}
        mock_mongo_repo.create.return_value = mock_product

        result = await mock_product_service.create(sample_product_create)

        assert result == mock_product
        mock_mongo_repo.create.assert_called_once()
        mock_elastic_repo.index_document.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_product_handles_search_error(
        self,
        mock_product_service: ProductService,
        mock_mongo_repo: MongoRepository,
        mock_elastic_repo: ElasticRepository,
        sample_product_create: ProductCreate,
    ) -> None:
        """Test that search indexing failure doesn't break creation."""
        mock_product = MagicMock(spec=Product)
        mock_product.id = "123"
        mock_product.model_dump.return_value = {"id": "123", "name": "Test"}
        mock_mongo_repo.create.return_value = mock_product
        mock_elastic_repo.index_document.side_effect = SearchError("Index failed")

        result = await mock_product_service.create(sample_product_create)

        assert result == mock_product


class TestProductServiceGetById:
    """Tests for getting product by ID."""

    @pytest.mark.asyncio
    @patch("arch_layer_prod_mongo_fast.models.product.Product")
    async def test_get_by_id_from_cache(
        self,
        mock_product_class: MagicMock,
        mock_product_service: ProductService,
        mock_redis_repo: RedisRepository,
    ) -> None:
        """Test getting product from cache."""
        cached_data = {
            "id": "507f1f77bcf86cd799439011",
            "name": "Cached Product",
            "price": "99.99",
            "stock": 10,
            "category": "Test",
            "is_active": True,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        }
        mock_redis_repo.get.return_value = cached_data

        mock_product = MagicMock(spec=Product)
        mock_product.name = "Cached Product"
        mock_product_class.return_value = mock_product

        result = await mock_product_service.get_by_id("507f1f77bcf86cd799439011")
        assert result.name == "Cached Product"

    @pytest.mark.asyncio
    async def test_get_by_id_from_database(
        self,
        mock_product_service: ProductService,
        mock_mongo_repo: MongoRepository,
        mock_redis_repo: RedisRepository,
    ) -> None:
        """Test getting product from database when cache miss."""
        mock_redis_repo.get.return_value = None

        mock_product = MagicMock(spec=Product)
        mock_product.model_dump.return_value = {"id": "123", "name": "DB Product"}
        mock_mongo_repo.get_by_id.return_value = mock_product

        result = await mock_product_service.get_by_id("123")

        assert result == mock_product
        mock_mongo_repo.get_by_id.assert_called_once_with("123")
        mock_redis_repo.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_handles_cache_error_on_read(
        self,
        mock_product_service: ProductService,
        mock_mongo_repo: MongoRepository,
        mock_redis_repo: RedisRepository,
    ) -> None:
        """Test handling cache read error."""
        mock_redis_repo.get.side_effect = CacheError("Cache failed")

        mock_product = MagicMock(spec=Product)
        mock_product.model_dump.return_value = {"id": "123", "name": "Product"}
        mock_mongo_repo.get_by_id.return_value = mock_product

        result = await mock_product_service.get_by_id("123")

        assert result == mock_product
        mock_mongo_repo.get_by_id.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_handles_cache_error_on_write(
        self,
        mock_product_service: ProductService,
        mock_mongo_repo: MongoRepository,
        mock_redis_repo: RedisRepository,
    ) -> None:
        """Test handling cache write error."""
        mock_redis_repo.get.return_value = None
        mock_redis_repo.set.side_effect = CacheError("Cache write failed")

        mock_product = MagicMock(spec=Product)
        mock_product.model_dump.return_value = {"id": "123", "name": "Product"}
        mock_mongo_repo.get_by_id.return_value = mock_product

        result = await mock_product_service.get_by_id("123")

        assert result == mock_product


class TestProductServiceUpdate:
    """Tests for product update."""

    @pytest.mark.asyncio
    async def test_update_product(
        self,
        mock_product_service: ProductService,
        mock_mongo_repo: MongoRepository,
        mock_redis_repo: RedisRepository,
        mock_elastic_repo: ElasticRepository,
        sample_product_update: ProductUpdate,
    ) -> None:
        """Test updating product invalidates cache and reindexes."""
        mock_product = MagicMock(spec=Product)
        mock_product.id = "123"
        mock_product.model_dump.return_value = {"id": "123", "name": "Updated"}
        mock_mongo_repo.update.return_value = mock_product

        result = await mock_product_service.update("123", sample_product_update)

        assert result == mock_product
        mock_mongo_repo.update.assert_called_once_with("123", sample_product_update)
        mock_redis_repo.delete.assert_called_once()
        mock_elastic_repo.index_document.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_handles_cache_error(
        self,
        mock_product_service: ProductService,
        mock_mongo_repo: MongoRepository,
        mock_redis_repo: RedisRepository,
        sample_product_update: ProductUpdate,
    ) -> None:
        """Test update continues when cache delete fails."""
        mock_product = MagicMock(spec=Product)
        mock_product.id = "123"
        mock_product.model_dump.return_value = {"id": "123", "name": "Updated"}
        mock_mongo_repo.update.return_value = mock_product
        mock_redis_repo.delete.side_effect = CacheError("Delete failed")

        result = await mock_product_service.update("123", sample_product_update)

        assert result == mock_product


class TestProductServiceDelete:
    """Tests for product deletion."""

    @pytest.mark.asyncio
    async def test_delete_product(
        self,
        mock_product_service: ProductService,
        mock_mongo_repo: MongoRepository,
        mock_redis_repo: RedisRepository,
        mock_elastic_repo: ElasticRepository,
    ) -> None:
        """Test product deletion clears cache and search."""
        await mock_product_service.delete("123")

        mock_mongo_repo.delete.assert_called_once_with("123")
        mock_redis_repo.delete.assert_called_once()
        mock_elastic_repo.delete_document.assert_called_once_with("123")

    @pytest.mark.asyncio
    async def test_delete_handles_cache_error(
        self,
        mock_product_service: ProductService,
        mock_mongo_repo: MongoRepository,
        mock_redis_repo: RedisRepository,
    ) -> None:
        """Test delete continues when cache delete fails."""
        mock_redis_repo.delete.side_effect = CacheError("Delete failed")

        await mock_product_service.delete("123")

        mock_mongo_repo.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_handles_search_error(
        self,
        mock_product_service: ProductService,
        mock_mongo_repo: MongoRepository,
        mock_elastic_repo: ElasticRepository,
    ) -> None:
        """Test delete continues when search delete fails."""
        mock_elastic_repo.delete_document.side_effect = SearchError("Search failed")

        await mock_product_service.delete("123")

        mock_mongo_repo.delete.assert_called_once()


class TestProductServiceList:
    """Tests for listing products."""

    @pytest.mark.asyncio
    async def test_list_all_products(
        self,
        mock_product_service: ProductService,
        mock_mongo_repo: MongoRepository,
    ) -> None:
        """Test listing all products."""
        mock_products = [MagicMock(spec=Product), MagicMock(spec=Product)]
        mock_mongo_repo.list_all.return_value = mock_products

        result = await mock_product_service.list_all()

        assert result == mock_products
        mock_mongo_repo.list_all.assert_called_once_with(
            skip=0,
            limit=100,
            category=None,
            is_active=None,
        )

    @pytest.mark.asyncio
    async def test_list_all_with_filters(
        self,
        mock_product_service: ProductService,
        mock_mongo_repo: MongoRepository,
    ) -> None:
        """Test listing products with filters."""
        mock_products = [MagicMock(spec=Product)]
        mock_mongo_repo.list_all.return_value = mock_products

        result = await mock_product_service.list_all(
            skip=10,
            limit=20,
            category="Electronics",
            is_active=True,
        )

        assert result == mock_products
        mock_mongo_repo.list_all.assert_called_once_with(
            skip=10,
            limit=20,
            category="Electronics",
            is_active=True,
        )


class TestProductServiceSearch:
    """Tests for search operations."""

    @pytest.mark.asyncio
    async def test_search(
        self,
        mock_product_service: ProductService,
        mock_elastic_repo: ElasticRepository,
    ) -> None:
        """Test full-text search."""
        mock_results = [{"id": "1", "name": "Product"}]
        mock_elastic_repo.search.return_value = mock_results

        result = await mock_product_service.search("test", size=5)

        assert result == mock_results
        mock_elastic_repo.search.assert_called_once_with("test", 5)

    @pytest.mark.asyncio
    async def test_search_by_category(
        self,
        mock_product_service: ProductService,
        mock_elastic_repo: ElasticRepository,
    ) -> None:
        """Test search by category."""
        mock_results = [{"id": "1", "category": "Electronics"}]
        mock_elastic_repo.search_by_category.return_value = mock_results

        result = await mock_product_service.search_by_category("Electronics")

        assert result == mock_results
        mock_elastic_repo.search_by_category.assert_called_once_with("Electronics")

    @pytest.mark.asyncio
    async def test_search_by_price_range(
        self,
        mock_product_service: ProductService,
        mock_elastic_repo: ElasticRepository,
    ) -> None:
        """Test search by price range."""
        mock_results = [{"id": "1", "price": 50.0}]
        mock_elastic_repo.search_by_price_range.return_value = mock_results

        result = await mock_product_service.search_by_price_range(10.0, 100.0)

        assert result == mock_results
        mock_elastic_repo.search_by_price_range.assert_called_once_with(10.0, 100.0)


class TestProductServiceReindex:
    """Tests for reindexing."""

    @pytest.mark.asyncio
    async def test_reindex_all(
        self,
        mock_product_service: ProductService,
        mock_mongo_repo: MongoRepository,
        mock_elastic_repo: ElasticRepository,
    ) -> None:
        """Test reindexing all products."""
        mock_product1 = MagicMock(spec=Product)
        mock_product1.model_dump.return_value = {"id": "1", "name": "Product 1"}
        mock_product2 = MagicMock(spec=Product)
        mock_product2.model_dump.return_value = {"id": "2", "name": "Product 2"}
        mock_mongo_repo.list_all.return_value = [mock_product1, mock_product2]

        result = await mock_product_service.reindex_all()

        assert result == 2
        mock_mongo_repo.list_all.assert_called_once_with(limit=10000)
        mock_elastic_repo.bulk_index.assert_called_once()


class TestProductServiceCache:
    """Tests for cache operations."""

    @pytest.mark.asyncio
    async def test_clear_cache(
        self,
        mock_product_service: ProductService,
        mock_redis_repo: RedisRepository,
    ) -> None:
        """Test clearing all product caches."""
        await mock_product_service.clear_cache()

        mock_redis_repo.delete_pattern.assert_called_once_with("product:*")


class TestProductServiceCount:
    """Tests for count operation."""

    @pytest.mark.asyncio
    async def test_count(
        self,
        mock_product_service: ProductService,
        mock_mongo_repo: MongoRepository,
    ) -> None:
        """Test getting product count."""
        mock_mongo_repo.count.return_value = 42

        result = await mock_product_service.count()

        assert result == 42
        mock_mongo_repo.count.assert_called_once()


class TestCacheKey:
    """Tests for cache key generation."""

    def test_cache_key_format(
        self,
        mock_product_service: ProductService,
    ) -> None:
        """Test cache key format."""
        key = mock_product_service._cache_key("123")  # noqa: SLF001
        assert key == "product:123"
