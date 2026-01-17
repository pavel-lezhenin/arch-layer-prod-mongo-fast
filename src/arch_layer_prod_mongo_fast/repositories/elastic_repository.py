"""Elasticsearch repository for search operations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from arch_layer_prod_mongo_fast.exceptions import SearchError

if TYPE_CHECKING:
    from elasticsearch import AsyncElasticsearch


class ElasticRepository:
    """Repository for Elasticsearch search operations."""

    def __init__(
        self,
        es_client: AsyncElasticsearch,
        index_name: str,
    ) -> None:
        """Initialize Elasticsearch repository.

        Args:
            es_client: Async Elasticsearch client
            index_name: Name of the index to use
        """
        self._client = es_client
        self._index = index_name

    async def create_index(self) -> None:
        """Create index with product mapping."""
        mapping = {
            "settings": {
                "analysis": {
                    "normalizer": {
                        "lowercase_normalizer": {
                            "type": "custom",
                            "filter": ["lowercase"],
                        }
                    }
                }
            },
            "mappings": {
                "properties": {
                    "id": {"type": "keyword"},
                    "name": {
                        "type": "text",
                        "fields": {"keyword": {"type": "keyword"}},
                    },
                    "description": {"type": "text"},
                    "price": {"type": "scaled_float", "scaling_factor": 100},
                    "stock": {"type": "integer"},
                    "category": {
                        "type": "keyword",
                        "normalizer": "lowercase_normalizer",
                    },
                    "is_active": {"type": "boolean"},
                    "created_at": {"type": "date"},
                    "updated_at": {"type": "date"},
                }
            },
        }

        try:
            exists = await self._client.indices.exists(index=self._index)
            if not exists:
                await self._client.indices.create(
                    index=self._index,
                    body=mapping,
                )
        except Exception as e:
            msg = f"Failed to create index: {e}"
            raise SearchError(msg) from e

    async def index_document(
        self,
        doc_id: str,
        document: dict[str, Any],
    ) -> None:
        """Index a document."""
        try:
            await self._client.index(
                index=self._index,
                id=doc_id,
                document=document,
            )
        except Exception as e:
            msg = f"Failed to index document: {e}"
            raise SearchError(msg) from e

    async def delete_document(self, doc_id: str) -> None:
        """Delete a document by ID."""
        try:
            await self._client.delete(
                index=self._index,
                id=doc_id,
            )
        except Exception as e:
            msg = f"Failed to delete document: {e}"
            raise SearchError(msg) from e

    async def search(
        self,
        query: str,
        size: int = 10,
    ) -> list[dict[str, Any]]:
        """Full-text search across products."""
        search_query = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["name^2", "description", "category"],
                    "fuzziness": "AUTO",
                }
            },
            "size": size,
        }

        try:
            response = await self._client.search(
                index=self._index,
                body=search_query,
            )
            return [hit["_source"] for hit in response["hits"]["hits"]]
        except Exception as e:
            msg = f"Failed to search: {e}"
            raise SearchError(msg) from e

    async def search_by_category(
        self,
        category: str,
        size: int = 100,
    ) -> list[dict[str, Any]]:
        """Search products by category (case-insensitive)."""
        search_query = {
            "query": {
                "term": {
                    "category": category.lower(),
                }
            },
            "size": size,
        }

        try:
            response = await self._client.search(
                index=self._index,
                body=search_query,
            )
            return [hit["_source"] for hit in response["hits"]["hits"]]
        except Exception as e:
            msg = f"Failed to search by category: {e}"
            raise SearchError(msg) from e

    async def search_by_price_range(
        self,
        min_price: float,
        max_price: float,
        size: int = 100,
    ) -> list[dict[str, Any]]:
        """Search products within a price range."""
        search_query = {
            "query": {
                "range": {
                    "price": {
                        "gte": min_price,
                        "lte": max_price,
                    }
                }
            },
            "size": size,
        }

        try:
            response = await self._client.search(
                index=self._index,
                body=search_query,
            )
            return [hit["_source"] for hit in response["hits"]["hits"]]
        except Exception as e:
            msg = f"Failed to search by price range: {e}"
            raise SearchError(msg) from e

    async def bulk_index(self, documents: list[dict[str, Any]]) -> None:
        """Bulk index multiple documents."""
        if not documents:
            return

        try:
            operations = []
            for doc in documents:
                operations.append({"index": {"_index": self._index, "_id": doc["id"]}})
                operations.append(doc)

            await self._client.bulk(operations=operations)
        except Exception as e:
            msg = f"Failed to bulk index: {e}"
            raise SearchError(msg) from e

    async def delete_index(self) -> None:
        """Delete the index (use with caution)."""
        try:
            await self._client.indices.delete(
                index=self._index,
            )
        except Exception as e:
            msg = f"Failed to delete index: {e}"
            raise SearchError(msg) from e
