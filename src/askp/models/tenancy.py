"""Tenancy models: Organization and Project.

These are the root of ASKP's multi-tenant design (Decision #3 — multi-tenant from line one):

- **Organization** is the top-level tenant and isolation boundary. Per spec invariant INV-4,
  data never crosses between Organizations.
- **Project** subdivides an Organization for grouping and cost attribution.

The ``slug`` columns are human-friendly identifiers (e.g. ``acme``, ``chatbot-prod``) used in
URLs and CLIs. An Organization slug is globally unique; a Project slug is unique *within* its
Organization (enforced by the composite unique constraint), so two orgs can both have a
``prod`` project.

Note: unlike most modules we deliberately do **not** ``from __future__ import annotations`` here.
SQLModel inspects the real annotation objects to wire up ``Relationship``; stringized
annotations break that resolution.
"""

import uuid

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, Relationship

from askp.models.base import Base


class Organization(Base, table=True):
    __tablename__ = "organization"

    name: str = Field(index=True)
    slug: str = Field(index=True, unique=True)

    projects: list["Project"] = Relationship(back_populates="organization")


class Project(Base, table=True):
    __tablename__ = "project"
    __table_args__ = (
        UniqueConstraint("organization_id", "slug", name="uq_project_org_slug"),
    )

    organization_id: uuid.UUID = Field(foreign_key="organization.id", index=True)
    name: str
    slug: str = Field(index=True)

    organization: Organization | None = Relationship(back_populates="projects")
