"""The credential Vault (spec §7.4).

The Vault is where Provider Credentials live, encrypted at rest. It sits between two subsystems:
:mod:`askp.security.encryption` (the cryptography) and :mod:`askp.models.credential` (the
storage), and exposes a deliberately small surface:

- ``put`` — write or rotate a credential (the Admin API's job). Encrypts before the secret ever
  reaches the database.
- ``resolve`` — fetch and decrypt a credential for the Gateway at forward time. This is the only
  read path, and it returns the plaintext **in-process only** (INV-1); nothing hands it back out
  through an API.

``resolve`` matches the :class:`askp.gateway.credentials.CredentialResolver` protocol, so the
Vault is a drop-in replacement for the development env resolver in the Gateway.

The AAD bound into the ciphertext is ``"<org>:<provider>"``. Because the same string scopes the
database row *and* authenticates the decryption, a credential is locked to its tenant both by the
query and by the cipher (§6.4 / INV-4).
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlmodel import select

from askp.models.credential import ProviderCredential
from askp.security.encryption import Cipher


class Vault:
    """Stores and retrieves encrypted Provider Credentials."""

    def __init__(
        self,
        *,
        session_factory: async_sessionmaker[AsyncSession],
        cipher: Cipher,
    ) -> None:
        self._session_factory = session_factory
        self._cipher = cipher

    @staticmethod
    def _aad(org: str, provider: str) -> str:
        return f"{org}:{provider}"

    async def put(self, *, org: str, provider: str, secret: str) -> None:
        """Write or rotate the credential for ``(org, provider)``.

        Idempotent on the key: an existing credential is re-encrypted and overwritten (rotation),
        otherwise a new row is inserted. The plaintext ``secret`` is encrypted here and never
        persisted in the clear.
        """

        ciphertext = self._cipher.encrypt(secret, aad=self._aad(org, provider))

        async with self._session_factory() as session:
            existing = await self._fetch(session, org=org, provider=provider)
            if existing is None:
                session.add(ProviderCredential(org=org, provider=provider, ciphertext=ciphertext))
            else:
                existing.ciphertext = ciphertext
                existing.key_version = 1
                session.add(existing)
            await session.commit()

    async def resolve(self, *, org: str, provider: str) -> str | None:
        """Return the decrypted credential for ``(org, provider)``, or None if there is none."""

        async with self._session_factory() as session:
            row = await self._fetch(session, org=org, provider=provider)

        if row is None:
            return None
        return self._cipher.decrypt(row.ciphertext, aad=self._aad(org, provider))

    async def delete(self, *, org: str, provider: str) -> bool:
        """Remove the credential for ``(org, provider)``. Returns False if there was none."""

        async with self._session_factory() as session:
            row = await self._fetch(session, org=org, provider=provider)
            if row is None:
                return False
            await session.delete(row)
            await session.commit()
            return True

    @staticmethod
    async def _fetch(
        session: AsyncSession, *, org: str, provider: str
    ) -> ProviderCredential | None:
        statement = select(ProviderCredential).where(
            ProviderCredential.org == org,
            ProviderCredential.provider == provider,
        )
        result = await session.execute(statement)
        return result.scalar_one_or_none()
