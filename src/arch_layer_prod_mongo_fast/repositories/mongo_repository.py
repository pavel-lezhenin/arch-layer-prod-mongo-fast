"""MongoDB repository implementation using Beanie."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from beanie.operators import RegEx

from arch_layer_prod_mongo_fast.exceptions import DatabaseError, NotFoundError

if TYPE_CHECKING:
    from arch_layer_prod_mongo_fast.models.product import (
        Product,
        ProductCreate,
        ProductUpdate,
    )


class MongoRepository:
    """Repository for MongoDB operations using Beanie ODM."""

    async def create(self, data: ProductCreate) -> Product:
        """Create a new product in MongoDB."""
        from arch_layer_prod_mongo_fast.models.product import Product  # noqa: PLC0415

        try:
            product = Product(**data.model_dump())
            await product.insert()
            return product  # noqa: TRY300
        except Exception as e:
            msg = f"Failed to create product: {e}"
            raise DatabaseError(msg) from e

    async def get_by_id(self, product_id: str) -> Product:
        """Get product by ID."""
        from arch_layer_prod_mongo_fast.models.product import Product  # noqa: PLC0415

        try:
            product = await Product.get(product_id)
            if not product:
                msg = f"Product {product_id} not found"
                raise NotFoundError(msg)  # noqa: TRY301
            return product  # noqa: TRY300
        except NotFoundError:
            raise
        except Exception as e:
            msg = f"Failed to get product: {e}"
            raise DatabaseError(msg) from e

    async def update(
        self,
        product_id: str,
        data: ProductUpdate,
    ) -> Product:
        """Update an existing product."""
        product = await self.get_by_id(product_id)

        try:
            update_data = data.model_dump(exclude_unset=True)
            if update_data:
                update_data["updated_at"] = datetime.now(UTC)
                for field, value in update_data.items():
                    setattr(product, field, value)
                await product.save()
            return product  # noqa: TRY300
        except Exception as e:
            msg = f"Failed to update product: {e}"
            raise DatabaseError(msg) from e

    async def delete(self, product_id: str) -> None:
        """Delete a product by ID."""
        product = await self.get_by_id(product_id)

        try:
            await product.delete()
        except Exception as e:
            msg = f"Failed to delete product: {e}"
            raise DatabaseError(msg) from e

    async def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
        category: str | None = None,
        is_active: bool | None = None,
    ) -> list[Product]:
        """List products with optional filtering."""
        from arch_layer_prod_mongo_fast.models.product import Product  # noqa: PLC0415

        try:
            query: dict[str, Any] = {}
            if category:
                query["category"] = category
            if is_active is not None:
                query["is_active"] = is_active

            return (
                await Product.find(query)
                .sort("-created_at")
                .skip(skip)
                .limit(limit)
                .to_list()
            )
        except Exception as e:
            msg = f"Failed to list products: {e}"
            raise DatabaseError(msg) from e

    async def search_by_name(self, query: str) -> list[Product]:
        """Search products by name using regex."""
        from arch_layer_prod_mongo_fast.models.product import Product  # noqa: PLC0415

        try:
            return (
                await Product.find(RegEx(Product.name, query, "i"))
                .sort("-created_at")
                .to_list()
            )
        except Exception as e:
            msg = f"Failed to search products: {e}"
            raise DatabaseError(msg) from e

    async def get_by_category(self, category: str) -> list[Product]:
        """Get all products in a specific category."""
        from arch_layer_prod_mongo_fast.models.product import Product  # noqa: PLC0415

        try:
            return (
                await Product.find(Product.category == category)
                .sort("-created_at")
                .to_list()
            )
        except Exception as e:
            msg = f"Failed to get products by category: {e}"
            raise DatabaseError(msg) from e

    async def count(self) -> int:
        """Count total products."""
        from arch_layer_prod_mongo_fast.models.product import Product  # noqa: PLC0415

        try:
            return await Product.count()
        except Exception as e:
            msg = f"Failed to count products: {e}"
            raise DatabaseError(msg) from e
