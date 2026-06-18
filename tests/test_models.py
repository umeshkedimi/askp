"""Tests for the tenancy models (Organization, Project).

These exercise real persistence through an AsyncSession on in-memory SQLite, proving the models
map to a database and the relationships work.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from askp.models import Organization, Project


async def test_create_organization_assigns_uuid_and_timestamps(session: AsyncSession) -> None:
    org = Organization(name="Acme", slug="acme")
    session.add(org)
    await session.commit()
    await session.refresh(org)

    assert isinstance(org.id, uuid.UUID)
    assert org.created_at is not None
    assert org.updated_at is not None


async def test_project_belongs_to_organization(session: AsyncSession) -> None:
    org = Organization(name="Acme", slug="acme")
    session.add(org)
    await session.commit()
    await session.refresh(org)

    project = Project(organization_id=org.id, name="Chatbot Prod", slug="chatbot-prod")
    session.add(project)
    await session.commit()

    loaded = (
        await session.execute(select(Project).where(Project.slug == "chatbot-prod"))
    ).scalar_one()
    assert loaded.organization_id == org.id


async def test_organization_slug_is_unique(session: AsyncSession) -> None:
    session.add(Organization(name="Acme", slug="acme"))
    await session.commit()

    session.add(Organization(name="Acme Duplicate", slug="acme"))
    with pytest.raises(IntegrityError):
        await session.commit()


async def test_project_slug_unique_within_org_but_reusable_across_orgs(
    session: AsyncSession,
) -> None:
    org_a = Organization(name="Org A", slug="org-a")
    org_b = Organization(name="Org B", slug="org-b")
    session.add(org_a)
    session.add(org_b)
    await session.commit()
    await session.refresh(org_a)
    await session.refresh(org_b)

    # Same project slug "prod" is fine in two different organizations.
    session.add(Project(organization_id=org_a.id, name="Prod", slug="prod"))
    session.add(Project(organization_id=org_b.id, name="Prod", slug="prod"))
    await session.commit()

    # But a duplicate slug within the same organization is rejected.
    session.add(Project(organization_id=org_a.id, name="Prod Again", slug="prod"))
    with pytest.raises(IntegrityError):
        await session.commit()
