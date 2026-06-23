"""Shared pytest fixtures.

``conftest.py`` is auto-discovered by pytest; fixtures defined here are available to every test
without importing them.

We test the data layer against **in-memory SQLite** (via ``aiosqlite``) so the suite runs with
no Docker and no real Postgres. Our models use portable column types, so they map cleanly to
both SQLite (tests) and PostgreSQL (production) — a nice forcing function for DB-agnostic design.
Redis is replaced with a small stub, since the readiness probe only needs a ``ping``.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

import askp.models  # noqa: F401 — ensure all tables are registered on SQLModel.metadata
from askp.app import create_app
from askp.config import Environment, Settings

SQLITE_MEMORY_DSN = "sqlite+aiosqlite://"


class FakeRedis:
    """In-memory async stand-in for the bits of Redis our code uses.

    Enough for the readiness probe (``ping``/``aclose``) and the revocation list
    (``set``/``exists``). Expiry is not simulated in real time; the recorded TTL is kept in
    ``ttls`` so tests can assert on it.
    """

    def __init__(self) -> None:
        self._store: dict[str, str] = {}
        self.ttls: dict[str, int] = {}

    async def ping(self) -> bool:
        return True

    async def aclose(self) -> None:
        return None

    async def set(self, name: str, value: str, ex: int | None = None) -> bool:
        self._store[name] = value
        if ex is not None:
            self.ttls[name] = ex
        return True

    async def exists(self, *names: str) -> int:
        return sum(1 for name in names if name in self._store)


@pytest.fixture
def settings() -> Settings:
    """Test settings: development env, SQLite DB so the readiness probe passes."""

    return Settings(environment=Environment.development, database_url=SQLITE_MEMORY_DSN)


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    """A FastAPI TestClient. Swaps in a fake Redis after lifespan startup."""

    app = create_app(settings)
    with TestClient(app) as test_client:
        app.state.redis = FakeRedis()
        yield test_client


@pytest_asyncio.fixture
async def session() -> AsyncIterator[AsyncSession]:
    """A real AsyncSession on a shared in-memory SQLite engine with the schema created.

    ``StaticPool`` keeps a single underlying connection so the in-memory database persists for
    the whole test (a fresh connection would otherwise get an empty, separate database).
    """

    engine = create_async_engine(
        SQLITE_MEMORY_DSN,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with factory() as db_session:
        yield db_session

    await engine.dispose()
