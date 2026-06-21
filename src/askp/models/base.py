"""Shared model base: a UUID primary key and created/updated timestamps.

Every ASKP entity gets:

- a **UUID** primary key (not an auto-increment integer). UUIDs are unguessable, generated
  client-side without a round-trip, and safe to expose in URLs/tokens — all of which matter for
  a multi-tenant security product where leaking sequential IDs would leak business information.
- ``created_at`` / ``updated_at`` timestamps, kept in UTC.

``Base`` is **not** a table itself (no ``table=True``); concrete models inherit from it.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime
from sqlmodel import Field, SQLModel

# ``DateTime(timezone=True)`` => TIMESTAMPTZ on PostgreSQL, so timestamps are unambiguous across
# timezones — important for audit trails. SQLite has no native tz type but round-trips the value,
# so tests still pass. We pass it via ``sa_type`` (not ``sa_column``) so SQLModel builds a fresh
# Column for each subclass; a single shared ``Column`` instance cannot be attached to two tables.
# SQLModel accepts a type *instance* here at runtime, though its stub annotates ``sa_type`` as a
# class — hence the localized ignores.
_TZ_DATETIME = DateTime(timezone=True)


def utcnow() -> datetime:
    """Timezone-aware current time in UTC. Used for default timestamps."""

    return datetime.now(UTC)


class Base(SQLModel):
    """Common columns for all ASKP tables."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(
        default_factory=utcnow,
        sa_type=_TZ_DATETIME,  # type: ignore[call-overload]
        nullable=False,
    )
    updated_at: datetime = Field(
        default_factory=utcnow,
        sa_type=_TZ_DATETIME,  # type: ignore[call-overload]
        nullable=False,
        # ``onupdate`` runs on every UPDATE, refreshing the timestamp automatically.
        sa_column_kwargs={"onupdate": utcnow},
    )
