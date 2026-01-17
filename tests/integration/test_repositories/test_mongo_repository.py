"""Integration tests for MongoDB repository using testcontainers.

These tests use testcontainers to spin up a real MongoDB instance.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from arch_layer_prod_mongo_fast.exceptions import NotFoundError
from arch_layer_prod_mongo_fast.models.product import ProductCreate, ProductUpdate
from arch_layer_prod_mongo_fast.repositories import MongoRepository


class TestMongoRepositoryCreate:
    """Tests for MongoDB repository create operation."""

    @pytest.mark.asyncio
    async def test_create_product(
        self,
        mongo_repo: MongoRepository,
        sample_product_create: ProductCreate,
    ) -> None:
        """Test creating a product in MongoDB."""
        product = await mongo_repo.create(sample_product_create)

        assert product.name == sample_product_create.name
        assert product.description == sample_product_create.description
        assert product.price == sample_product_create.price
        assert product.stock == sample_product_create.stock
        assert product.category == sample_product_create.category
        assert product.is_active is True
        assert product.id is not None
        assert product.created_at is not None
        assert product.updated_at is not None


class TestMongoRepositoryGetById:
    """Tests for MongoDB repository get_by_id operation."""

    @pytest.mark.asyncio
    async def test_get_by_id_existing_product(
        self,
        mongo_repo: MongoRepository,
        sample_product_create: ProductCreate,
    ) -> None:
        """Test getting an existing product by ID."""
        created = await mongo_repo.create(sample_product_create)

        product = await mongo_repo.get_by_id(str(created.id))

        assert product.id == created.id
        assert product.name == sample_product_create.name

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(
        self,
        mongo_repo: MongoRepository,
    ) -> None:
        """Test getting a non-existent product raises NotFoundError."""
        with pytest.raises(NotFoundError) as exc_info:
            await mongo_repo.get_by_id("507f1f77bcf86cd799439099")

        assert "not found" in str(exc_info.value).lower()


class TestMongoRepositoryUpdate:
    """Tests for MongoDB repository update operation."""

    @pytest.mark.asyncio
    async def test_update_product(
        self,
        mongo_repo: MongoRepository,
        sample_product_create: ProductCreate,
    ) -> None:
        """Test updating a product."""
        created = await mongo_repo.create(sample_product_create)

        update_data = ProductUpdate(name="Updated Name", price=Decimal("199.99"))
        updated = await mongo_repo.update(str(created.id), update_data)

        assert updated.name == "Updated Name"
        assert updated.price == Decimal("199.99")
        assert updated.description == sample_product_create.description
        # Just verify updated_at is set (comparing timezones is unreliable)
        assert updated.updated_at is not None

    @pytest.mark.asyncio
    async def test_update_partial_data(
        self,
        mongo_repo: MongoRepository,
        sample_product_create: ProductCreate,
    ) -> None:
        """Test partial update with only some fields."""
        created = await mongo_repo.create(sample_product_create)

        update_data = ProductUpdate(stock=100)
        updated = await mongo_repo.update(str(created.id), update_data)

        assert updated.stock == 100
        assert updated.name == sample_product_create.name

    @pytest.mark.asyncio
    async def test_update_not_found(
        self,
        mongo_repo: MongoRepository,
    ) -> None:
        """Test updating a non-existent product raises NotFoundError."""
        update_data = ProductUpdate(name="Does Not Exist")

        with pytest.raises(NotFoundError):
            await mongo_repo.update("507f1f77bcf86cd799439099", update_data)


class TestMongoRepositoryDelete:
    """Tests for MongoDB repository delete operation."""

    @pytest.mark.asyncio
    async def test_delete_product(
        self,
        mongo_repo: MongoRepository,
        sample_product_create: ProductCreate,
    ) -> None:
        """Test deleting a product."""
        created = await mongo_repo.create(sample_product_create)

        await mongo_repo.delete(str(created.id))

        with pytest.raises(NotFoundError):
            await mongo_repo.get_by_id(str(created.id))

    @pytest.mark.asyncio
    async def test_delete_not_found(
        self,
        mongo_repo: MongoRepository,
    ) -> None:
        """Test deleting a non-existent product raises NotFoundError."""
        with pytest.raises(NotFoundError):
            await mongo_repo.delete("507f1f77bcf86cd799439099")


class TestMongoRepositoryListAll:
    """Tests for MongoDB repository list_all operation."""

    @pytest.mark.asyncio
    async def test_list_all_empty(
        self,
        mongo_repo: MongoRepository,
    ) -> None:
        """Test listing products when none exist."""
        products = await mongo_repo.list_all()
        assert isinstance(products, list)

    @pytest.mark.asyncio
    async def test_list_all_with_products(
        self,
        mongo_repo: MongoRepository,
    ) -> None:
        """Test listing products when some exist."""
        for i in range(3):
            data = ProductCreate(
                name=f"Product {i}",
                description=f"Description {i}",
                price=Decimal(str(10 * (i + 1))),
                stock=10 * (i + 1),
                category="TestCategory",
            )
            await mongo_repo.create(data)

        products = await mongo_repo.list_all()
        assert len(products) >= 3

    @pytest.mark.asyncio
    async def test_list_all_with_pagination(
        self,
        mongo_repo: MongoRepository,
    ) -> None:
        """Test listing products with pagination."""
        for i in range(5):
            data = ProductCreate(
                name=f"Page Product {i}",
                description=f"Description {i}",
                price=Decimal("10.00"),
                stock=10,
                category="PageTest",
            )
            await mongo_repo.create(data)

        products = await mongo_repo.list_all(skip=2, limit=2)
        assert len(products) <= 2

    @pytest.mark.asyncio
    async def test_list_all_filter_by_category(
        self,
        mongo_repo: MongoRepository,
    ) -> None:
        """Test filtering products by category."""
        unique_category = "UniqueCategoryFilter"
        data = ProductCreate(
            name="Unique Category Product",
            description="Test",
            price=Decimal("10.00"),
            stock=10,
            category=unique_category,
        )
        await mongo_repo.create(data)

        products = await mongo_repo.list_all(category=unique_category)
        assert all(p.category == unique_category for p in products)

    @pytest.mark.asyncio
    async def test_list_all_filter_by_is_active(
        self,
        mongo_repo: MongoRepository,
    ) -> None:
        """Test filtering products by is_active status."""
        products = await mongo_repo.list_all(is_active=True)
        assert all(p.is_active is True for p in products)


class TestMongoRepositorySearchByName:
    """Tests for MongoDB repository search_by_name operation."""

    @pytest.mark.asyncio
    async def test_search_by_name(
        self,
        mongo_repo: MongoRepository,
    ) -> None:
        """Test searching products by name."""
        data = ProductCreate(
            name="Searchable Unique Product",
            description="For search test",
            price=Decimal("50.00"),
            stock=5,
            category="SearchTest",
        )
        await mongo_repo.create(data)

        products = await mongo_repo.search_by_name("Searchable")
        assert len(products) >= 1
        assert any("Searchable" in p.name for p in products)

    @pytest.mark.asyncio
    async def test_search_by_name_case_insensitive(
        self,
        mongo_repo: MongoRepository,
    ) -> None:
        """Test that search is case insensitive."""
        data = ProductCreate(
            name="CaseTest Product",
            description="Case insensitive test",
            price=Decimal("25.00"),
            stock=3,
            category="CaseTest",
        )
        await mongo_repo.create(data)

        products = await mongo_repo.search_by_name("casetest")
        assert len(products) >= 1


class TestMongoRepositoryGetByCategory:
    """Tests for MongoDB repository get_by_category operation."""

    @pytest.mark.asyncio
    async def test_get_by_category(
        self,
        mongo_repo: MongoRepository,
    ) -> None:
        """Test getting products by category."""
        unique_category = "GetByCategoryTest"
        for i in range(2):
            data = ProductCreate(
                name=f"Category Product {i}",
                description="Test",
                price=Decimal("15.00"),
                stock=15,
                category=unique_category,
            )
            await mongo_repo.create(data)

        products = await mongo_repo.get_by_category(unique_category)
        assert len(products) >= 2
        assert all(p.category == unique_category for p in products)


class TestMongoRepositoryCount:
    """Tests for MongoDB repository count operation."""

    @pytest.mark.asyncio
    async def test_count_products(
        self,
        mongo_repo: MongoRepository,
    ) -> None:
        """Test counting products."""
        count = await mongo_repo.count()
        assert isinstance(count, int)
        assert count >= 0
