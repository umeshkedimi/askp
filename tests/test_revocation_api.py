"""Tests for the admin revocation endpoint (POST /v1/admin/revocations)."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from askp.app import create_app
from askp.config import Environment, Settings
from askp.security.revocation import RevocationList

from .conftest import FakeRedis

ADMIN_KEY = "test-admin-key"
AUTH = {"Authorization": f"Bearer {ADMIN_KEY}"}


@pytest.fixture
def admin() -> Iterator[tuple[TestClient, FakeRedis]]:
    settings = Settings(
        environment=Environment.development,
        database_url="sqlite+aiosqlite://",
        admin_api_key=ADMIN_KEY,
    )
    app = create_app(settings)
    fake = FakeRedis()
    with TestClient(app) as client:
        app.state.revocations = RevocationList(fake)
        yield client, fake


def test_revoke_requires_admin(admin: tuple[TestClient, FakeRedis]) -> None:
    client, _fake = admin
    resp = client.post("/v1/admin/revocations", json={"jti": "at_1"})
    assert resp.status_code == 401


def test_revoke_jti(admin: tuple[TestClient, FakeRedis]) -> None:
    client, fake = admin
    resp = client.post("/v1/admin/revocations", headers=AUTH, json={"jti": "at_1"})
    assert resp.status_code == 204
    # The entry exists and its TTL defaults to the configured Access Token lifetime.
    assert fake.ttls["askp:revoked:jti:at_1"] == 600


def test_revoke_family(admin: tuple[TestClient, FakeRedis]) -> None:
    client, fake = admin
    resp = client.post(
        "/v1/admin/revocations", headers=AUTH, json={"tf": "tf_1", "ttl_seconds": 120}
    )
    assert resp.status_code == 204
    assert fake.ttls["askp:revoked:tf:tf_1"] == 120


def test_revoke_requires_a_target(admin: tuple[TestClient, FakeRedis]) -> None:
    client, _fake = admin
    # Neither jti nor tf -> validation error.
    resp = client.post("/v1/admin/revocations", headers=AUTH, json={})
    assert resp.status_code == 422
