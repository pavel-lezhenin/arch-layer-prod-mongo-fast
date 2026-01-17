"""Tests for Elasticsearch repository."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock

import pytest

from arch_layer_prod_mongo_fast.repositories.elastic_repository import (
    ElasticRepository,
)

if TYPE_CHECKING:
    from elasticsearch import AsyncElasticsearch


@pytest.fixture
def mock_es() -> AsyncElasticsearch:
    """Create a mock Elasticsearch client."""
    mock = MagicMock()
    mock.indices = MagicMock()
    mock.indices.exists = AsyncMock()
    mock.indices.create = AsyncMock()
    mock.indices.delete = AsyncMock()
    mock.index = AsyncMock()
    mock.delete = AsyncMock()
    mock.search = AsyncMock()
    mock.bulk = AsyncMock()
    return mock


@pytest.fixture
def elastic_repo(mock_es: AsyncElasticsearch) -> ElasticRepository:
    """Create Elasticsearch repository with mock client."""
    return ElasticRepository(mock_es, "test_index")


class TestElasticRepository:
    """Tests for Elasticsearch repository."""

    @pytest.mark.asyncio
    async def test_create_index(
        self,
        elastic_repo: ElasticRepository,
        mock_es: AsyncElasticsearch,
    ) -> None:
        """Test index creation."""
        mock_es.indices.exists.return_value = False
        await elastic_repo.create_index()
        mock_es.indices.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_index_document(
        self,
        elastic_repo: ElasticRepository,
        mock_es: AsyncElasticsearch,
    ) -> None:
        """Test document indexing."""
        doc = {"id": "123", "name": "Test"}
        await elastic_repo.index_document("123", doc)
        mock_es.index.assert_called_once()

    @pytest.mark.asyncio
    async def test_search(
        self,
        elastic_repo: ElasticRepository,
        mock_es: AsyncElasticsearch,
    ) -> None:
        """Test search operation."""
        mock_es.search.return_value = {
            "hits": {
                "hits": [
                    {"_source": {"id": "1", "name": "Product 1"}},
                    {"_source": {"id": "2", "name": "Product 2"}},
                ]
            }
        }
        results = await elastic_repo.search("test query")
        assert len(results) == 2
        assert results[0]["name"] == "Product 1"

    @pytest.mark.asyncio
    async def test_delete_document(
        self,
        elastic_repo: ElasticRepository,
        mock_es: AsyncElasticsearch,
    ) -> None:
        """Test document deletion."""
        await elastic_repo.delete_document("123")
        mock_es.delete.assert_called_once()
