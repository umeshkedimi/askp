"""Tests for the admin credential endpoints (PUT/DELETE /v1/admin/...)."""

from collections.abc import Iterator
from pathlib import Path
from typing import cast

import anyio
import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel, select

import askp.models  # noqa: F401 — register tables on SQLModel.metadata
from askp.app import create_app
from askp.config import Environment, Settings
from askp.models.credential import ProviderCredential
from askp.security.encryption import generate_kek

ADMIN_KEY = "test-admin-key"
AUTH = {"Authorization": f"Bearer {ADMIN_KEY}"}


async def _create_schema(db_url: str) -> None:
    engine = create_async_engine(db_url)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    await engine.dispose()


async def _stored_rows(db_url: str) -> list[tuple[str, str, str]]:
    engine = create_async_engine(db_url)
    factory = async_sessionmaker(engine, class_=AsyncSession)
    async with factory() as session:
        rows = (await session.execute(select(ProviderCredential))).scalars().all()
        result = [(r.org, r.provider, r.ciphertext) for r in rows]
    await engine.dispose()
    return result


@pytest.fixture
def admin(tmp_path: Path) -> Iterator[tuple[TestClient, str]]:
    # A real file DB so the app's engine and our verification queries share state.
    db_url = f"sqlite+aiosqlite:///{tmp_path}/askp.db"
    anyio.run(_create_schema, db_url)
    settings = Settings(
        environment=Environment.development,
        database_url=db_url,
        admin_api_key=ADMIN_KEY,
        vault_kek=generate_kek(),
    )
    with TestClient(create_app(settings)) as client:
        yield client, db_url


def _put(
    client: TestClient, provider: str, org: str, secret: str, **headers: str
) -> httpx.Response:
    response = client.put(
        f"/v1/admin/providers/{provider}/credential",
        headers=headers,
        json={"org": org, "secret": secret},
    )
    return cast(httpx.Response, response)


def test_put_requires_admin(admin: tuple[TestClient, str]) -> None:
    client, _db = admin
    resp = _put(client, "openai", "org_acme", "sk-123")
    assert resp.status_code == 401


def test_put_stores_ciphertext(admin: tuple[TestClient, str]) -> None:
    client, db_url = admin
    resp = _put(client, "openai", "org_acme", "sk-SECRET-123", **AUTH)
    assert resp.status_code == 204

    rows = anyio.run(_stored_rows, db_url)
    assert len(rows) == 1
    org, provider, ciphertext = rows[0]
    assert (org, provider) == ("org_acme", "openai")
    assert "sk-SECRET-123" not in ciphertext  # encrypted at rest


def test_put_is_idempotent_rotation(admin: tuple[TestClient, str]) -> None:
    client, db_url = admin
    assert _put(client, "openai", "org_acme", "sk-old", **AUTH).status_code == 204
    assert _put(client, "openai", "org_acme", "sk-new", **AUTH).status_code == 204
    # Rotation overwrites in place — still one row.
    assert len(anyio.run(_stored_rows, db_url)) == 1


def test_delete_removes_credential(admin: tuple[TestClient, str]) -> None:
    client, db_url = admin
    _put(client, "openai", "org_acme", "sk-123", **AUTH)

    resp = client.delete(
        "/v1/admin/providers/openai/credential", params={"org": "org_acme"}, headers=AUTH
    )
    assert resp.status_code == 204
    assert anyio.run(_stored_rows, db_url) == []


def test_delete_absent_is_404(admin: tuple[TestClient, str]) -> None:
    client, _db = admin
    resp = client.delete(
        "/v1/admin/providers/openai/credential", params={"org": "ghost"}, headers=AUTH
    )
    assert resp.status_code == 404
