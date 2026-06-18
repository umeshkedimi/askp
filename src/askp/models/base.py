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

from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    """Timezone-aware current time in UTC. Used for default timestamps."""

    return datetime.now(UTC)


class Base(SQLModel):
    """Common columns for all ASKP tables."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=utcnow, nullable=False)
    updated_at: datetime = Field(
        default_factory=utcnow,
        nullable=False,
        # ``onupdate`` runs on every UPDATE, refreshing the timestamp automatically.
        sa_column_kwargs={"onupdate": utcnow},
    )
