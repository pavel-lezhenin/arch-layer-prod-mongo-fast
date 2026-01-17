"""Root pytest configuration.

This conftest just registers plugins.
Actual fixtures are in:
- tests/unit/conftest.py - fixtures for unit tests (mocks)
- tests/integration/conftest.py - fixtures for integration tests (testcontainers)
"""

from __future__ import annotations

# Pytest will automatically discover conftest.py files in subdirectories
