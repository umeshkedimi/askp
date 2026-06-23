"""Tests for the token issuance endpoint (POST /v1/tokens)."""

from collections.abc import Iterator
from typing import cast

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from askp.app import create_app
from askp.config import Environment, Settings

ADMIN_KEY = "test-admin-key"
SQLITE = "sqlite+aiosqlite://"


def _app(admin_key: str | None) -> FastAPI:
    settings = Settings(
        environment=Environment.development,
        database_url=SQLITE,
        admin_api_key=admin_key,
    )
    return create_app(settings)


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(_app(ADMIN_KEY)) as test_client:
        yield test_client


def _issue(client: TestClient, **headers: str) -> httpx.Response:
    response = client.post(
        "/v1/tokens",
        headers=headers,
        json={
            "subject": "agent:1",
            "org": "org_acme",
            "project": "proj",
            "scopes": ["provider:openai:model:gpt-4o:chat.completions"],
        },
    )
    return cast(httpx.Response, response)


def test_issue_requires_admin_key(client: TestClient) -> None:
    resp = _issue(client)
    assert resp.status_code == 401
    assert resp.headers["www-authenticate"] == "Bearer"


def test_issue_rejects_wrong_key(client: TestClient) -> None:
    resp = _issue(client, Authorization="Bearer wrong")
    assert resp.status_code == 401


def test_issue_returns_a_decodable_token(client: TestClient) -> None:
    resp = _issue(client, Authorization=f"Bearer {ADMIN_KEY}")
    assert resp.status_code == 200
    body = resp.json()

    assert body["token_type"] == "Bearer"
    assert body["access_token"].startswith("askp_at_")
    assert body["expires_in"] == 600
    assert body["scopes"] == ["provider:openai:model:gpt-4o:chat.completions"]

    # The returned token verifies against the app's issuer and carries the claims we asked for.
    issuer = client.app.state.token_issuer  # type: ignore[attr-defined]
    claims = issuer.decode(body["access_token"])
    assert claims.sub == "agent:1"
    assert claims.org == "org_acme"
    assert claims.jti == body["jti"]


def test_issue_disabled_when_no_admin_key_configured() -> None:
    with TestClient(_app(None)) as client:
        resp = _issue(client, Authorization="Bearer anything")
        assert resp.status_code == 503
