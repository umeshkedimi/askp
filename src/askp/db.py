"""Async database engine and session management.

ASKP uses **async SQLAlchemy 2.0** (via SQLModel) so the Gateway's hot path never blocks a
worker thread on I/O. The pieces:

- **Engine** — a pool of connections to PostgreSQL, created once per process. The
  ``create_async_engine`` call is lazy: it does not open a connection until one is needed, so
  constructing it cannot fail.
- **Session factory** — ``async_sessionmaker`` produces ``AsyncSession`` objects, the unit of
  work for a single logical operation (usually one request).
- **get_session** — a FastAPI dependency that yields a session per request and guarantees it is
  closed afterwards.

``expire_on_commit=False`` keeps ORM objects usable after ``commit()`` (otherwise attribute
access would trigger a fresh lazy load — awkward in async code).
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi import Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


class Database:
    """Owns the async engine and session factory for one process."""

    def __init__(self, dsn: str, *, echo: bool = False) -> None:
        # pool_pre_ping checks a connection is alive before use, avoiding errors from
        # connections the database closed while idle.
        self.engine: AsyncEngine = create_async_engine(dsn, echo=echo, pool_pre_ping=True)
        self.session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
            self.engine,
            expire_on_commit=False,
            class_=AsyncSession,
        )

    async def check(self) -> bool:
        """Return True if a trivial query succeeds. Used by the readiness probe."""

        try:
            async with self.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    async def dispose(self) -> None:
        """Close all pooled connections. Called on application shutdown."""

        await self.engine.dispose()


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """FastAPI dependency yielding an :class:`AsyncSession` bound to this request.

    Usage in a route::

        @router.post("/things")
        async def create_thing(session: AsyncSession = Depends(get_session)) -> ...:
            ...

    The ``async with`` block ensures the session is closed even if the handler raises.
    """

    db: Database = request.app.state.db
    async with db.session_factory() as session:
        yield session
