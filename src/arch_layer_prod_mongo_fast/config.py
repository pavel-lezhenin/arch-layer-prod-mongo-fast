"""Application configuration using pydantic-settings."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_title: str = Field(
        default="Layered Architecture Demo",
        description="Application title",
    )
    app_version: str = Field(default="0.1.0", description="Application version")
    app_debug: bool = Field(default=False, description="Debug mode")

    # Logging
    environment: str = Field(
        default="production",
        description="Environment: development, staging, production",
    )
    log_level: str = Field(
        default="INFO",
        description="Log level: DEBUG, INFO, WARNING, ERROR",
    )
    log_file: str | None = Field(
        default=None,
        description="Log file path for Loki/Promtail (JSON format)",
    )

    mongodb_uri: str = Field(
        default="mongodb://localhost:27017",
        description="MongoDB connection URI",
    )
    mongodb_database: str = Field(
        default="arch_layer_demo",
        description="MongoDB database name",
    )

    redis_uri: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URI",
    )
    redis_cache_ttl: int = Field(
        default=300,
        description="Redis cache TTL in seconds",
    )

    elasticsearch_uri: str = Field(
        default="http://localhost:9200",
        description="Elasticsearch URI",
    )
    elasticsearch_index: str = Field(
        default="products",
        description="Elasticsearch index name",
    )


def get_settings() -> Settings:
    """Get application settings instance."""
    return Settings()
