"""Tests for the health and readiness endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

from askp import __version__


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body == {"status": "ok", "service": "askp", "version": __version__}


def test_ready_returns_ready_when_dependencies_healthy(client: TestClient) -> None:
    response = client.get("/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["checks"] == {"database": True, "redis": True}


def test_openapi_schema_is_served(client: TestClient) -> None:
    """FastAPI auto-generates an OpenAPI schema; confirm it is exposed and titled."""

    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["title"] == "ASKP — AI Secure Key Protocol"
