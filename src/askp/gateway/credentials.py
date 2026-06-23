"""The credential-resolution seam (spec §6.3 step 9, INV-1, INV-4).

The Gateway must obtain the real Provider Credential *in-boundary*, only after pre-flight checks
pass, and strictly within the token's Organization (§6.4). It depends on the small
:class:`CredentialResolver` protocol rather than a concrete class, so the implementation can vary
without touching the route.

The production implementation is the encrypted :class:`askp.vault.Vault`; tests substitute a
trivial stub. (An environment-variable resolver lived here during Increment 3 as a placeholder
and was retired once the Vault landed.)
"""

from __future__ import annotations

from typing import Protocol


class CredentialResolver(Protocol):
    """Resolves a provider credential for a given Organization."""

    async def resolve(self, *, org: str, provider: str) -> str | None: ...
