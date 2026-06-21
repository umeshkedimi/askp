"""Alembic migration environment, configured for ASKP's async engine.

Key points for learners:

- We pull the database URL from ASKP settings (``ASKP_DATABASE_URL``) rather than hard-coding it
  in ``alembic.ini`` — one source of truth, shared with the running app.
- ``target_metadata = SQLModel.metadata`` lets ``alembic revision --autogenerate`` diff the
  models against the database to draft new migrations. Importing ``askp.models`` registers every
  table on that metadata.
- The engine is async (asyncpg / aiosqlite), so online migrations run inside ``asyncio`` and use
  ``connection.run_sync`` to drive Alembic's synchronous migration API.
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlmodel import SQLModel

import askp.models  # noqa: F401 — registers all tables on SQLModel.metadata
from askp.config import get_settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Point Alembic at the same database the application uses.
config.set_main_option("sqlalchemy.url", get_settings().database_url)

target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    """Generate SQL without a DB connection (``alembic upgrade --sql``)."""

    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        render_as_batch=connection.dialect.name == "sqlite",
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Open an async engine and run migrations within a synchronous bridge."""

    section = config.get_section(config.config_ini_section, {})
    connectable = async_engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
