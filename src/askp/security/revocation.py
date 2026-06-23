"""The revocation list — instant token revocation (spec §7.3, invariant INV-5).

ASKP's tokens are short-lived JWTs the Gateway can verify without a database round-trip. That
buys speed but not revocability, so we pair it with a **revocation list** in Redis: the Gateway
checks every token's ``jti`` (and token-family ``tf``) here on each request (pipeline step
6.3-③), and an admin can revoke a token instantly by adding its id.

Self-bounding size: a revocation entry only needs to outlive the token it revokes. Once the
token's ``exp`` passes, the normal expiry check rejects it anyway — so we give each entry a TTL
equal to the token's *remaining* lifetime (:func:`ttl_until`) and Redis evicts it automatically.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime
from typing import Protocol

# Key namespaces in Redis. Namespacing keeps revocation data from colliding with the budget /
# rate-limit counters that will share this Redis instance later.
_JTI_PREFIX = "askp:revoked:jti:"
_TF_PREFIX = "askp:revoked:tf:"


class RedisLike(Protocol):
    """The slice of the Redis async API the revocation list needs.

    Depending on this Protocol instead of the concrete client means any object with these two
    methods works — the real ``redis.asyncio.Redis`` in production and a lightweight fake in
    tests — and ``mypy --strict`` stays happy without the full client's type surface.
    """

    async def set(self, name: str, value: str, ex: int | None = ...) -> object: ...
    async def exists(self, *names: str) -> int: ...


def ttl_until(expires_at: datetime, now: datetime | None = None) -> int:
    """Seconds from ``now`` until ``expires_at``, rounded up, with a floor of 1.

    A floor of 1 keeps a just-expiring (or already-expired) token revoked for at least a tick,
    rather than passing ``ex=0`` which Redis rejects.
    """

    now = now or datetime.now(UTC)
    seconds = math.ceil((expires_at - now).total_seconds())
    return max(seconds, 1)


class RevocationList:
    """Reads and writes the revocation list. Written by the Issuer/Admin, read by the Gateway."""

    def __init__(self, redis: RedisLike) -> None:
        self._redis = redis

    async def revoke_jti(self, jti: str, ttl_seconds: int) -> None:
        """Revoke a single token by its ``jti``."""
        await self._redis.set(_JTI_PREFIX + jti, "1", ex=max(ttl_seconds, 1))

    async def revoke_family(self, tf: str, ttl_seconds: int) -> None:
        """Revoke an entire token family by its ``tf`` (e.g. on refresh-token compromise)."""
        await self._redis.set(_TF_PREFIX + tf, "1", ex=max(ttl_seconds, 1))

    async def is_revoked(self, *, jti: str, tf: str | None = None) -> bool:
        """Return True if the token's ``jti`` — or its family ``tf`` — has been revoked.

        A single ``EXISTS`` over both keys returns how many are present; any hit means revoked.
        """

        keys = [_JTI_PREFIX + jti]
        if tf is not None:
            keys.append(_TF_PREFIX + tf)
        return await self._redis.exists(*keys) > 0
