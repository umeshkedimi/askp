"""Tests for the revocation list (askp.security.revocation)."""

from datetime import UTC, datetime, timedelta

from askp.security.revocation import RevocationList, ttl_until

from .conftest import FakeRedis


def test_ttl_until_future_is_positive() -> None:
    exp = datetime.now(UTC) + timedelta(seconds=300)
    assert 295 <= ttl_until(exp) <= 300


def test_ttl_until_past_floors_to_one() -> None:
    exp = datetime.now(UTC) - timedelta(hours=1)
    assert ttl_until(exp) == 1


async def test_unrevoked_token_is_not_revoked() -> None:
    revocations = RevocationList(FakeRedis())
    assert await revocations.is_revoked(jti="at_1") is False


async def test_revoke_jti_marks_token_revoked() -> None:
    redis = FakeRedis()
    revocations = RevocationList(redis)

    await revocations.revoke_jti("at_1", ttl_seconds=300)

    assert await revocations.is_revoked(jti="at_1") is True
    # Other tokens are unaffected.
    assert await revocations.is_revoked(jti="at_2") is False
    # The entry's TTL matches the token's remaining lifetime.
    assert redis.ttls["askp:revoked:jti:at_1"] == 300


async def test_family_revocation_revokes_member_tokens() -> None:
    revocations = RevocationList(FakeRedis())

    await revocations.revoke_family("tf_1", ttl_seconds=300)

    # A token whose own jti is not listed is still revoked via its family.
    assert await revocations.is_revoked(jti="at_99", tf="tf_1") is True
    # ...but only when we check against that family.
    assert await revocations.is_revoked(jti="at_99") is False


async def test_revoke_floors_zero_ttl_to_one() -> None:
    redis = FakeRedis()
    await RevocationList(redis).revoke_jti("at_1", ttl_seconds=0)
    assert redis.ttls["askp:revoked:jti:at_1"] == 1
