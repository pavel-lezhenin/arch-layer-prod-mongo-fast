"""Data access layer repositories."""

from __future__ import annotations

from arch_layer_prod_mongo_fast.repositories.elastic_repository import (
    ElasticRepository,
)
from arch_layer_prod_mongo_fast.repositories.mongo_repository import MongoRepository
from arch_layer_prod_mongo_fast.repositories.redis_repository import RedisRepository

__all__ = [
    "ElasticRepository",
    "MongoRepository",
    "RedisRepository",
]
