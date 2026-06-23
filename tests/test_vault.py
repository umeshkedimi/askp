"""Tests for the credential Vault (askp.vault)."""

import base64
from collections.abc import AsyncIterator

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, select

import askp.models  # noqa: F401 — register tables on SQLModel.metadata
from askp.models.credential import ProviderCredential
from askp.security.encryption import Cipher, generate_kek
from askp.vault import Vault


@pytest_asyncio.fixture
async def vault() -> AsyncIterator[Vault]:
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    # A fixed KEK so the same Vault instance can decrypt what it wrote within the test.
    cipher = Cipher(kek=base64.b64decode(generate_kek()))
    yield Vault(session_factory=factory, cipher=cipher)

    await engine.dispose()


async def test_put_then_resolve_round_trips(vault: Vault) -> None:
    await vault.put(org="org_acme", provider="openai", secret="sk-live-123")
    assert await vault.resolve(org="org_acme", provider="openai") == "sk-live-123"


async def test_resolve_absent_returns_none(vault: Vault) -> None:
    assert await vault.resolve(org="org_acme", provider="openai") is None


async def test_secret_is_encrypted_at_rest(vault: Vault) -> None:
    await vault.put(org="org_acme", provider="openai", secret="sk-live-123")

    # Read the raw row straight from the database: it must not contain the plaintext.
    async with vault._session_factory() as session:  # noqa: SLF001 — test inspects storage
        row = (await session.execute(select(ProviderCredential))).scalar_one()
    assert "sk-live-123" not in row.ciphertext


async def test_tenant_isolation(vault: Vault) -> None:
    await vault.put(org="org_acme", provider="openai", secret="sk-acme")
    # A different org has no credential, even for the same provider.
    assert await vault.resolve(org="org_other", provider="openai") is None
    # And the right tenant still gets theirs.
    assert await vault.resolve(org="org_acme", provider="openai") == "sk-acme"


async def test_rotation_overwrites_in_place(vault: Vault) -> None:
    await vault.put(org="org_acme", provider="openai", secret="sk-old")
    await vault.put(org="org_acme", provider="openai", secret="sk-new")

    assert await vault.resolve(org="org_acme", provider="openai") == "sk-new"

    # Rotation updates the existing row rather than creating a second one.
    async with vault._session_factory() as session:  # noqa: SLF001
        rows = (await session.execute(select(ProviderCredential))).scalars().all()
    assert len(rows) == 1
