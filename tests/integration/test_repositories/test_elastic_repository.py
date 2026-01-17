"""Integration tests for Elasticsearch repository using testcontainers.

These tests use testcontainers to spin up a real Elasticsearch instance.
"""

from __future__ import annotations

import pytest

from arch_layer_prod_mongo_fast.repositories.elastic_repository import (
    ElasticRepository,
)


class TestElasticRepositoryIntegration:
    """Integration tests for Elasticsearch repository using real ES."""

    @pytest.mark.asyncio
    async def test_create_index(
        self,
        elastic_repo: ElasticRepository,
    ) -> None:
        """Test creating an index."""
        await elastic_repo.create_index()
        # If no exception, index was created successfully

    @pytest.mark.asyncio
    async def test_index_and_search_document(
        self,
        elastic_repo: ElasticRepository,
    ) -> None:
        """Test indexing and searching a document."""
        await elastic_repo.create_index()

        doc = {
            "id": "test-123",
            "name": "Test Product",
            "description": "A test product for searching",
            "price": 99.99,
            "category": "Electronics",
            "stock": 10,
            "is_active": True,
        }
        await elastic_repo.index_document("test-123", doc)

        # Wait for ES to index the document
        import asyncio

        await asyncio.sleep(1)

        results = await elastic_repo.search("Test Product")
        assert len(results) >= 1
        assert any(r["id"] == "test-123" for r in results)

    @pytest.mark.asyncio
    async def test_search_by_category(
        self,
        elastic_repo: ElasticRepository,
    ) -> None:
        """Test searching by category."""
        await elastic_repo.create_index()

        doc1 = {
            "id": "cat-1",
            "name": "Product 1",
            "description": "First product",
            "price": 50.00,
            "category": "UniqueCategory",
            "stock": 5,
            "is_active": True,
        }
        doc2 = {
            "id": "cat-2",
            "name": "Product 2",
            "description": "Second product",
            "price": 75.00,
            "category": "UniqueCategory",
            "stock": 8,
            "is_active": True,
        }
        await elastic_repo.index_document("cat-1", doc1)
        await elastic_repo.index_document("cat-2", doc2)

        import asyncio

        await asyncio.sleep(1)

        results = await elastic_repo.search_by_category("UniqueCategory")
        assert len(results) >= 2

    @pytest.mark.asyncio
    async def test_search_by_price_range(
        self,
        elastic_repo: ElasticRepository,
    ) -> None:
        """Test searching by price range."""
        await elastic_repo.create_index()

        docs = [
            {"id": "price-1", "name": "Cheap", "price": 10.00, "category": "Test"},
            {"id": "price-2", "name": "Medium", "price": 50.00, "category": "Test"},
            {"id": "price-3", "name": "Expensive", "price": 200.00, "category": "Test"},
        ]
        for doc in docs:
            await elastic_repo.index_document(doc["id"], doc)

        import asyncio

        await asyncio.sleep(1)

        results = await elastic_repo.search_by_price_range(20.0, 100.0)
        # Should find Medium (50.00) but not Cheap (10.00) or Expensive (200.00)
        prices = [r.get("price", 0) for r in results]
        assert all(20.0 <= p <= 100.0 for p in prices if p > 0)

    @pytest.mark.asyncio
    async def test_delete_document(
        self,
        elastic_repo: ElasticRepository,
    ) -> None:
        """Test deleting a document."""
        await elastic_repo.create_index()

        doc = {
            "id": "delete-test",
            "name": "To Delete",
            "price": 30.00,
            "category": "Test",
        }
        await elastic_repo.index_document("delete-test", doc)

        import asyncio

        await asyncio.sleep(1)

        await elastic_repo.delete_document("delete-test")

        await asyncio.sleep(1)

        results = await elastic_repo.search("To Delete")
        assert not any(r.get("id") == "delete-test" for r in results)

    @pytest.mark.asyncio
    async def test_bulk_index(
        self,
        elastic_repo: ElasticRepository,
    ) -> None:
        """Test bulk indexing multiple documents."""
        await elastic_repo.create_index()

        docs = [
            {"id": "bulk-1", "name": "Bulk Product 1", "price": 10.00},
            {"id": "bulk-2", "name": "Bulk Product 2", "price": 20.00},
            {"id": "bulk-3", "name": "Bulk Product 3", "price": 30.00},
        ]
        await elastic_repo.bulk_index(docs)

        import asyncio

        await asyncio.sleep(1)

        results = await elastic_repo.search("Bulk Product")
        assert len(results) >= 3
