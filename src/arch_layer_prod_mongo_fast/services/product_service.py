"""Product service with integrated cache and search."""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Any

from arch_layer_prod_mongo_fast.exceptions import CacheError, SearchError
from arch_layer_prod_mongo_fast.utils import log_operation

if TYPE_CHECKING:
    from arch_layer_prod_mongo_fast.models.product import (
        Product,
        ProductCreate,
        ProductUpdate,
    )
    from arch_layer_prod_mongo_fast.repositories.elastic_repository import (
        ElasticRepository,
    )
    from arch_layer_prod_mongo_fast.repositories.mongo_repository import (
        MongoRepository,
    )
    from arch_layer_prod_mongo_fast.repositories.redis_repository import (
        RedisRepository,
    )


class ProductService:
    """Business logic for product operations with cache and search."""

    def __init__(
        self,
        mongo_repo: MongoRepository,
        redis_repo: RedisRepository,
        elastic_repo: ElasticRepository,
    ) -> None:
        """Initialize product service with all repositories.

        Args:
            mongo_repo: MongoDB repository for persistence
            redis_repo: Redis repository for caching
            elastic_repo: Elasticsearch repository for search
        """
        self._mongo = mongo_repo
        self._cache = redis_repo
        self._search = elastic_repo

    def _cache_key(self, product_id: str) -> str:
        """Generate cache key for a product."""
        return f"product:{product_id}"

    @log_operation("Create product")
    async def create(self, data: ProductCreate) -> Product:
        """Create a new product with search indexing."""
        product = await self._mongo.create(data)

        with contextlib.suppress(SearchError):
            await self._search.index_document(
                doc_id=str(product.id),
                document=product.model_dump(),
            )

        return product

    @log_operation("Get product by ID")
    async def get_by_id(self, product_id: str) -> Product:
        """Get product by ID with caching."""
        cache_key = self._cache_key(product_id)

        try:
            cached = await self._cache.get(cache_key)
            if cached:
                from arch_layer_prod_mongo_fast.models.product import (  # noqa: PLC0415
                    Product,
                )

                return Product(**cached)
        except CacheError:
            pass

        product = await self._mongo.get_by_id(product_id)

        with contextlib.suppress(CacheError):
            await self._cache.set(cache_key, product.model_dump())

        return product

    @log_operation("Update product")
    async def update(
        self,
        product_id: str,
        data: ProductUpdate,
    ) -> Product:
        """Update product and invalidate cache."""
        product = await self._mongo.update(product_id, data)

        cache_key = self._cache_key(product_id)
        with contextlib.suppress(CacheError):
            await self._cache.delete(cache_key)

        with contextlib.suppress(SearchError):
            await self._search.index_document(
                doc_id=str(product.id),
                document=product.model_dump(),
            )

        return product

    @log_operation("Delete product")
    async def delete(self, product_id: str) -> None:
        """Delete product and clear cache/search."""
        await self._mongo.delete(product_id)

        cache_key = self._cache_key(product_id)
        with contextlib.suppress(CacheError):
            await self._cache.delete(cache_key)

        with contextlib.suppress(SearchError):
            await self._search.delete_document(product_id)

    @log_operation("List products")
    async def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
        category: str | None = None,
        is_active: bool | None = None,
    ) -> list[Product]:
        """List products with optional filtering."""
        return await self._mongo.list_all(
            skip=skip,
            limit=limit,
            category=category,
            is_active=is_active,
        )

    @log_operation("Search products")
    async def search(
        self,
        query: str,
        size: int = 10,
    ) -> list[dict[str, Any]]:
        """Full-text search using Elasticsearch."""
        return await self._search.search(query, size)

    async def search_by_category(self, category: str) -> list[dict[str, Any]]:
        """Search products by category using Elasticsearch."""
        return await self._search.search_by_category(category)

    async def search_by_price_range(
        self,
        min_price: float,
        max_price: float,
    ) -> list[dict[str, Any]]:
        """Search products by price range."""
        return await self._search.search_by_price_range(
            min_price,
            max_price,
        )

    @log_operation("Reindex all products")
    async def reindex_all(self) -> int:
        """Reindex all products in Elasticsearch."""
        products = await self._mongo.list_all(limit=10000)

        documents = [product.model_dump() for product in products]
        await self._search.bulk_index(documents)

        return len(documents)

    async def clear_cache(self) -> None:
        """Clear all product caches."""
        await self._cache.delete_pattern("product:*")

    async def count(self) -> int:
        """Get total product count."""
        return await self._mongo.count()
