"""ProviderCredential: an encrypted-at-rest provider secret (spec §7.4).

This is the Vault's storage table. It holds the **ciphertext only** — the encrypted blob produced
by :mod:`askp.security.encryption` — never the plaintext key (INV-1). The plaintext exists only
transiently in memory when the Gateway forwards a request.

Keyed by ``(org, provider)``: one stored credential per provider per tenant. ``org`` is the same
Organization identifier the Gateway reads from the token's ``org`` claim, so credential lookup is
naturally tenant-scoped (§6.4).
"""

from sqlalchemy import UniqueConstraint
from sqlmodel import Field

from askp.models.base import Base


class ProviderCredential(Base, table=True):
    __tablename__ = "provider_credential"
    __table_args__ = (
        UniqueConstraint("org", "provider", name="uq_credential_org_provider"),
    )

    # Tenant identifier (matches the token's ``org`` claim), not a wildcard scope value.
    org: str = Field(index=True)
    provider: str
    # The envelope-encrypted secret (Cipher.encrypt output). Opaque to the database.
    ciphertext: str
    # Which KEK generation wrapped this credential's data key; lets a future rotation re-wrap.
    key_version: int = Field(default=1)
