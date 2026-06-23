"""provider_credential: encrypted provider secrets

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-23

Adds the Vault's storage table (spec §7.4). The ``ciphertext`` column holds the envelope-encrypted
blob only; plaintext credentials are never stored. ``(org, provider)`` is unique — one credential
per provider per tenant.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "provider_credential",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("org", sa.String(), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("ciphertext", sa.String(), nullable=False),
        sa.Column("key_version", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("org", "provider", name="uq_credential_org_provider"),
    )
    op.create_index("ix_provider_credential_org", "provider_credential", ["org"])


def downgrade() -> None:
    op.drop_index("ix_provider_credential_org", table_name="provider_credential")
    op.drop_table("provider_credential")
