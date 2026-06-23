"""Provider Credential resolution (spec §6.3 step 9, INV-1, INV-4).

The Gateway must obtain the real Provider Credential *in-boundary*, only after pre-flight checks
pass, and strictly within the token's Organization (§6.4). Encrypted-at-rest storage with
write-only access is the **Vault** (Increment 4). Until then this placeholder reads keys from the
environment so the proxy can be exercised end-to-end.

We depend on the :class:`CredentialResolver` Protocol, not a concrete class, so swapping the env
resolver for the Vault later is a one-line wiring change.
"""

from __future__ import annotations

import os
from typing import Protocol


class CredentialResolver(Protocol):
    """Resolves a provider credential for a given Organization."""

    async def resolve(self, *, org: str, provider: str) -> str | None: ...


class EnvCredentialResolver:
    """Development credential source: reads ``ASKP_PROVIDER_<PROVIDER>_KEY`` from the environment.

    Placeholder for the Vault. It ignores ``org`` (single-tenant dev), but the signature already
    takes ``org`` so the Vault can enforce per-Organization isolation (INV-4) without changing
    any caller.
    """

    async def resolve(self, *, org: str, provider: str) -> str | None:
        return os.environ.get(f"ASKP_PROVIDER_{provider.upper()}_KEY")
