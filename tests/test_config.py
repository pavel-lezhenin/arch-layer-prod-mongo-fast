"""Tests for application configuration."""

from __future__ import annotations

import os
from unittest.mock import patch

from arch_layer_prod_mongo_fast.config import Settings, get_settings


class TestSettings:
    """Tests for Settings class."""

    def test_default_settings(self) -> None:
        """Test default settings values without env vars."""
        # Clear env vars that might affect defaults
        env_vars = [
            "MONGODB_DATABASE",
            "MONGODB_URI",
            "REDIS_URI",
            "ELASTICSEARCH_URI",
            "APP_TITLE",
            "APP_VERSION",
            "APP_DEBUG",
        ]
        with patch.dict(os.environ, {}, clear=True):
            for var in env_vars:
                os.environ.pop(var, None)

            settings = Settings(
                _env_file=None,  # Ignore .env file
            )

            assert settings.app_title == "Layered Architecture Demo"
            assert settings.app_version == "0.1.0"
            assert settings.app_debug is False
            assert settings.mongodb_uri == "mongodb://localhost:27017"
            assert settings.mongodb_database == "arch_layer_demo"
            assert settings.redis_uri == "redis://localhost:6379/0"
            assert settings.redis_cache_ttl == 300
            assert settings.elasticsearch_uri == "http://localhost:9200"
            assert settings.elasticsearch_index == "products"

    def test_custom_settings(self) -> None:
        """Test custom settings values."""
        settings = Settings(
            app_title="Custom App",
            app_version="1.0.0",
            app_debug=True,
            mongodb_uri="mongodb://custom:27017",
            mongodb_database="custom_db",
            redis_uri="redis://custom:6379/1",
            redis_cache_ttl=600,
            elasticsearch_uri="http://custom:9200",
            elasticsearch_index="custom_products",
            _env_file=None,  # Ignore .env file
        )

        assert settings.app_title == "Custom App"
        assert settings.app_version == "1.0.0"
        assert settings.app_debug is True
        assert settings.mongodb_uri == "mongodb://custom:27017"
        assert settings.mongodb_database == "custom_db"
        assert settings.redis_uri == "redis://custom:6379/1"
        assert settings.redis_cache_ttl == 600
        assert settings.elasticsearch_uri == "http://custom:9200"
        assert settings.elasticsearch_index == "custom_products"


class TestGetSettings:
    """Tests for get_settings function."""

    def test_get_settings_returns_settings_instance(self) -> None:
        """Test that get_settings returns a Settings instance."""
        settings = get_settings()
        assert isinstance(settings, Settings)
