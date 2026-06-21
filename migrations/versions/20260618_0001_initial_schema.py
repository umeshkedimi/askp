"""initial schema: organization, project

Revision ID: 0001
Revises:
Create Date: 2026-06-18

The first ASKP migration. Creates the tenancy tables (Organization, Project). Column types are
dialect-portable: ``sa.Uuid`` becomes native ``UUID`` on PostgreSQL and ``CHAR(32)`` on SQLite,
and ``sa.DateTime(timezone=True)`` becomes ``TIMESTAMPTZ`` on PostgreSQL.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "organization",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_organization_name", "organization", ["name"])
    op.create_index("ix_organization_slug", "organization", ["slug"], unique=True)

    op.create_table(
        "project",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organization.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "slug", name="uq_project_org_slug"),
    )
    op.create_index("ix_project_organization_id", "project", ["organization_id"])
    op.create_index("ix_project_slug", "project", ["slug"])


def downgrade() -> None:
    op.drop_table("project")
    op.drop_table("organization")
