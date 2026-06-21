"""Async Redis client.

Redis is ASKP's hot-path state store (spec & architecture): the **token revocation list**
(INV-5, instant revocation), **rate-limit counters**, and **budget counters**. These need
sub-millisecond reads on every Gateway request, which Postgres is not the right tool for.

Note on the module name: this file is ``askp.redis``, but ``import redis.asyncio`` below still
imports the *third-party* ``redis`` package — Python 3 uses absolute imports by default, so
there is no self-shadowing.
"""

from __future__ import annotations

import redis.asyncio as aioredis


def create_redis(url: str) -> aioredis.Redis:
    """Create an async Redis client from a connection URL.

    ``decode_responses=True`` means values come back as ``str`` rather than ``bytes`` — more
    ergonomic for the string keys/values ASKP stores (jti, counters). Like the DB engine, this
    is lazy and does not connect until the first command.
    """

    return aioredis.from_url(url, encoding="utf-8", decode_responses=True)


async def check_redis(client: aioredis.Redis) -> bool:
    """Return True if Redis answers PING. Used by the readiness probe."""

    try:
        return bool(await client.ping())
    except Exception:
        return False
