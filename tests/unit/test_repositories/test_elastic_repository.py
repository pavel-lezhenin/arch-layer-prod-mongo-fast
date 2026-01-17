"""Unit tests for ElasticRepository error handling."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from arch_layer_prod_mongo_fast.exceptions import SearchError
from arch_layer_prod_mongo_fast.repositories.elastic_repository import ElasticRepository


@pytest.fixture
def mock_es_client() -> MagicMock:
    """Create mock Elasticsearch client."""
    return MagicMock()


@pytest.fixture
def elastic_repo(mock_es_client: MagicMock) -> ElasticRepository:
    """Create ElasticRepository with mocked client."""
    return ElasticRepository(mock_es_client, index_name="test_products")


class TestCreateIndexError:
    """Tests for create_index error handling."""

    async def test_create_index_raises_search_error_on_failure(
        self,
        elastic_repo: ElasticRepository,
        mock_es_client: MagicMock,
    ) -> None:
        """Should raise SearchError when index creation fails."""
        mock_es_client.indices.exists = AsyncMock(side_effect=Exception("Connection failed"))

        with pytest.raises(SearchError, match="Failed to create index"):
            await elastic_repo.create_index()


class TestIndexDocumentError:
    """Tests for index_document error handling."""

    async def test_index_document_raises_search_error_on_failure(
        self,
        elastic_repo: ElasticRepository,
        mock_es_client: MagicMock,
    ) -> None:
        """Should raise SearchError when indexing fails."""
        mock_es_client.index = AsyncMock(side_effect=Exception("Index failed"))

        with pytest.raises(SearchError, match="Failed to index document"):
            await elastic_repo.index_document("doc1", {"name": "Test"})


class TestDeleteDocumentError:
    """Tests for delete_document error handling."""

    async def test_delete_document_raises_search_error_on_failure(
        self,
        elastic_repo: ElasticRepository,
        mock_es_client: MagicMock,
    ) -> None:
        """Should raise SearchError when deletion fails."""
        mock_es_client.delete = AsyncMock(side_effect=Exception("Delete failed"))

        with pytest.raises(SearchError, match="Failed to delete document"):
            await elastic_repo.delete_document("doc1")


class TestSearchError:
    """Tests for search error handling."""

    async def test_search_raises_search_error_on_failure(
        self,
        elastic_repo: ElasticRepository,
        mock_es_client: MagicMock,
    ) -> None:
        """Should raise SearchError when search fails."""
        mock_es_client.search = AsyncMock(side_effect=Exception("Search failed"))

        with pytest.raises(SearchError, match="Failed to search"):
            await elastic_repo.search("query")


class TestSearchByCategory:
    """Tests for search_by_category functionality."""

    async def test_search_by_category_lowercase_conversion(
        self,
        elastic_repo: ElasticRepository,
        mock_es_client: MagicMock,
    ) -> None:
        """Should convert category to lowercase for case-insensitive search."""
        mock_response = {
            "hits": {
                "hits": [
                    {"_source": {"id": "1", "name": "Product 1", "category": "Electronics"}},
                    {"_source": {"id": "2", "name": "Product 2", "category": "electronics"}},
                ]
            }
        }
        mock_es_client.search = AsyncMock(return_value=mock_response)

        # Test with uppercase
        results = await elastic_repo.search_by_category("Furniture")
        assert len(results) == 2

        # Verify query uses lowercase
        call_args = mock_es_client.search.call_args
        assert call_args[1]["body"]["query"]["term"]["category"] == "furniture"

    async def test_search_by_category_preserves_lowercase(
        self,
        elastic_repo: ElasticRepository,
        mock_es_client: MagicMock,
    ) -> None:
        """Should work correctly with already lowercase category."""
        mock_response = {"hits": {"hits": [{"_source": {"id": "1", "category": "electronics"}}]}}
        mock_es_client.search = AsyncMock(return_value=mock_response)

        results = await elastic_repo.search_by_category("electronics")
        assert len(results) == 1

        # Verify lowercase is preserved
        call_args = mock_es_client.search.call_args
        assert call_args[1]["body"]["query"]["term"]["category"] == "electronics"


class TestSearchByCategoryError:
    """Tests for search_by_category error handling."""

    async def test_search_by_category_raises_search_error_on_failure(
        self,
        elastic_repo: ElasticRepository,
        mock_es_client: MagicMock,
    ) -> None:
        """Should raise SearchError when category search fails."""
        mock_es_client.search = AsyncMock(side_effect=Exception("Category search failed"))

        with pytest.raises(SearchError, match="Failed to search by category"):
            await elastic_repo.search_by_category("electronics")


class TestSearchByPriceRangeError:
    """Tests for search_by_price_range error handling."""

    async def test_search_by_price_range_raises_search_error_on_failure(
        self,
        elastic_repo: ElasticRepository,
        mock_es_client: MagicMock,
    ) -> None:
        """Should raise SearchError when price range search fails."""
        mock_es_client.search = AsyncMock(side_effect=Exception("Price search failed"))

        with pytest.raises(SearchError, match="Failed to search by price range"):
            await elastic_repo.search_by_price_range(10.0, 100.0)


class TestBulkIndexError:
    """Tests for bulk_index error handling."""

    async def test_bulk_index_raises_search_error_on_failure(
        self,
        elastic_repo: ElasticRepository,
        mock_es_client: MagicMock,
    ) -> None:
        """Should raise SearchError when bulk indexing fails."""
        mock_es_client.bulk = AsyncMock(side_effect=Exception("Bulk failed"))

        with pytest.raises(SearchError, match="Failed to bulk index"):
            await elastic_repo.bulk_index([{"id": "1", "name": "Test"}])

    async def test_bulk_index_empty_documents_returns_early(
        self,
        elastic_repo: ElasticRepository,
        mock_es_client: MagicMock,
    ) -> None:
        """Should return early when documents list is empty."""
        await elastic_repo.bulk_index([])
        mock_es_client.bulk.assert_not_called()


class TestDeleteIndexError:
    """Tests for delete_index error handling."""

    async def test_delete_index_raises_search_error_on_failure(
        self,
        elastic_repo: ElasticRepository,
        mock_es_client: MagicMock,
    ) -> None:
        """Should raise SearchError when index deletion fails."""
        mock_es_client.indices.delete = AsyncMock(side_effect=Exception("Delete index failed"))

        with pytest.raises(SearchError, match="Failed to delete index"):
            await elastic_repo.delete_index()
