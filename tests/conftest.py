"""Shared pytest fixtures.

``conftest.py`` is auto-discovered by pytest; fixtures defined here are available to every test
without importing them.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from askp.app import create_app
from askp.config import Environment, Settings


@pytest.fixture
def settings() -> Settings:
    """Deterministic test settings (development env => readable console logs)."""

    return Settings(environment=Environment.development)


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    """A FastAPI TestClient wrapping a freshly built app.

    ``TestClient`` (from Starlette, backed by httpx) drives the app in-process — no real network
    or running server — and runs the ``lifespan`` startup/shutdown around the ``with`` block.
    """

    app = create_app(settings)
    with TestClient(app) as test_client:
        yield test_client
