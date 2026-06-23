"""End-to-end tests for the Gateway proxy route (askp.gateway.router).

We replace the upstream Provider with an httpx.MockTransport so no network is touched, and the
revocation list / credential resolver with in-memory stubs. The TokenIssuer created at app
startup mints the tokens we present, so signatures verify against the running app.
"""

from collections.abc import Callable, Iterator
from typing import cast

import anyio
import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from askp.app import create_app
from askp.config import Settings
from askp.security.revocation import RevocationList
from askp.security.tokens import TokenIssuer

from .conftest import FakeRedis

CHAT_SCOPE = "provider:openai:model:gpt-4o:chat.completions"

GatewayFixture = tuple[TestClient, TokenIssuer, list[httpx.Request]]


class StubCredentials:
    """Always resolves to one fixed key, standing in for the Vault."""

    def __init__(self, key: str) -> None:
        self._key = key

    async def resolve(self, *, org: str, provider: str) -> str | None:
        return self._key


def _make_handler(captured: list[httpx.Request]) -> Callable[[httpx.Request], httpx.Response]:
    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        if request.url.path == "/v1/messages":  # Anthropic streaming endpoint
            return httpx.Response(
                200,
                headers={"content-type": "text/event-stream"},
                content=b"data: hello\n\ndata: world\n\n",
            )
        return httpx.Response(
            200,
            json={
                "authorization": request.headers.get("authorization"),
                "x_api_key": request.headers.get("x-api-key"),
                "url": str(request.url),
            },
        )

    return handler


@pytest.fixture
def gateway(settings: Settings) -> Iterator[GatewayFixture]:
    app = create_app(settings)
    captured: list[httpx.Request] = []
    with TestClient(app) as client:
        # Swap the real datastore/network clients for in-memory stubs after startup.
        app.state.redis = FakeRedis()
        app.state.revocations = RevocationList(app.state.redis)
        app.state.credentials = StubCredentials("sk-real-provider-key")
        app.state.http = httpx.AsyncClient(transport=httpx.MockTransport(_make_handler(captured)))
        yield client, app.state.token_issuer, captured


def _mint(issuer: TokenIssuer, *, scopes: list[str], org: str = "org_acme") -> str:
    return issuer.issue(subject="agent:1", org=org, project="proj", scopes=scopes).token


def test_proxy_swaps_token_for_provider_credential(gateway: GatewayFixture) -> None:
    client, issuer, captured = gateway
    token = _mint(issuer, scopes=[CHAT_SCOPE])

    resp = client.post(
        "/v1/providers/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {token}"},
        json={"model": "gpt-4o", "messages": [{"role": "user", "content": "hi"}]},
    )

    assert resp.status_code == 200
    echoed = resp.json()
    # The provider sees its own key, NOT the ASKP token (INV-1).
    assert echoed["authorization"] == "Bearer sk-real-provider-key"
    assert "askp_at_" not in (echoed["authorization"] or "")
    assert echoed["url"] == "https://api.openai.com/v1/chat/completions"
    # And the request actually reached the (mocked) upstream once.
    assert len(captured) == 1


def test_missing_token_is_401(gateway: GatewayFixture) -> None:
    client, _issuer, _captured = gateway
    resp = client.post(
        "/v1/providers/openai/v1/chat/completions",
        json={"model": "gpt-4o"},
    )
    assert resp.status_code == 401
    assert resp.json()["error"] == "invalid_token"
    assert resp.headers["www-authenticate"] == "Bearer"


def test_revoked_token_is_401(gateway: GatewayFixture) -> None:
    client, issuer, _captured = gateway
    issued = issuer.issue(subject="agent:1", org="org_acme", project="proj", scopes=[CHAT_SCOPE])

    # Revoke the token's jti directly on the gateway's revocation list (an admin action).
    app = cast(FastAPI, client.app)
    revocations: RevocationList = app.state.revocations
    anyio.run(revocations.revoke_jti, issued.jti, 600)

    resp = client.post(
        "/v1/providers/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {issued.token}"},
        json={"model": "gpt-4o"},
    )
    assert resp.status_code == 401
    assert resp.json()["error"] == "token_revoked"


def test_insufficient_scope_is_403(gateway: GatewayFixture) -> None:
    client, issuer, _captured = gateway
    # Token only allows embeddings, but we request chat.completions.
    token = _mint(issuer, scopes=["provider:openai:model:gpt-4o:embeddings"])

    resp = client.post(
        "/v1/providers/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {token}"},
        json={"model": "gpt-4o", "messages": []},
    )
    assert resp.status_code == 403
    assert resp.json()["error"] == "insufficient_scope"


def test_unknown_provider_is_404(gateway: GatewayFixture) -> None:
    client, issuer, _captured = gateway
    token = _mint(issuer, scopes=[CHAT_SCOPE])
    resp = client.post(
        "/v1/providers/cohere/v1/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"model": "x"},
    )
    assert resp.status_code == 404
    assert resp.json()["error"] == "unsupported_operation"


def test_sse_stream_passes_through(gateway: GatewayFixture) -> None:
    client, issuer, _captured = gateway
    token = _mint(issuer, scopes=["provider:anthropic:model:claude-sonnet-4-6:messages"])

    resp = client.post(
        "/v1/providers/anthropic/v1/messages",
        headers={"Authorization": f"Bearer {token}"},
        json={"model": "claude-sonnet-4-6", "messages": []},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")
    assert resp.text == "data: hello\n\ndata: world\n\n"
