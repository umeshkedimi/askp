"""Tests for Access Token issuance and verification (askp.security.tokens)."""

from datetime import UTC, datetime, timedelta

import jwt
import pytest

from askp.security import keys
from askp.security.tokens import TOKEN_PREFIX, TokenIssuer

ISSUER = "https://askp.test"
AUDIENCE = "https://askp.test/gateway"


def make_issuer(ttl_seconds: int = 600) -> TokenIssuer:
    return TokenIssuer(
        signing_key=keys.generate(),
        issuer=ISSUER,
        audience=AUDIENCE,
        ttl_seconds=ttl_seconds,
    )


def test_issue_round_trips_claims() -> None:
    issuer = make_issuer()
    issued = issuer.issue(
        subject="agent:123",
        org="org_acme",
        project="proj_chatbot",
        scopes=["provider:openai:model:gpt-4o-mini:chat.completions"],
        budget_refs=["budget:proj_chatbot:daily"],
        token_family="tf_1",
    )

    claims = issuer.decode(issued.token)
    assert claims.iss == ISSUER
    assert claims.aud == AUDIENCE
    assert claims.sub == "agent:123"
    assert claims.org == "org_acme"
    assert claims.proj == "proj_chatbot"
    assert claims.scopes == ["provider:openai:model:gpt-4o-mini:chat.completions"]
    assert claims.bud == ["budget:proj_chatbot:daily"]
    assert claims.tf == "tf_1"
    assert claims.jti == issued.jti
    # Lifetime is the configured TTL.
    assert claims.exp - claims.iat == timedelta(seconds=600)


def test_token_has_transport_prefix() -> None:
    issued = make_issuer().issue(subject="user:1", org="o", project="p", scopes=[])
    assert issued.token.startswith(TOKEN_PREFIX)


def test_header_advertises_kid_and_eddsa() -> None:
    issuer = make_issuer()
    issued = issuer.issue(subject="user:1", org="o", project="p", scopes=[])

    header = jwt.get_unverified_header(issued.token.removeprefix(TOKEN_PREFIX))
    assert header["alg"] == "EdDSA"
    assert header["kid"] == issuer.kid


def test_rejects_alg_none() -> None:
    # A token forged with alg:none must never be accepted (spec §4.1).
    issuer = make_issuer()
    forged = jwt.encode(
        {"iss": ISSUER, "aud": AUDIENCE, "sub": "x", "org": "o", "proj": "p",
         "scopes": [], "jti": "at_x",
         "iat": datetime.now(UTC), "exp": datetime.now(UTC) + timedelta(minutes=5)},
        key=None,
        algorithm="none",
    )
    with pytest.raises(jwt.InvalidAlgorithmError):
        issuer.decode(TOKEN_PREFIX + forged)


def test_rejects_foreign_signature() -> None:
    # A token signed by a different key fails signature verification.
    issuer = make_issuer()
    other = make_issuer()
    issued = other.issue(subject="user:1", org="o", project="p", scopes=[])
    with pytest.raises(jwt.InvalidSignatureError):
        issuer.decode(issued.token)


def test_rejects_expired_token() -> None:
    # Mint a token whose lifetime is already in the past via the injectable clock.
    issuer = make_issuer(ttl_seconds=60)
    past = datetime.now(UTC) - timedelta(hours=1)
    issued = issuer.issue(subject="user:1", org="o", project="p", scopes=[], now=past)
    with pytest.raises(jwt.ExpiredSignatureError):
        issuer.decode(issued.token)


def test_rejects_wrong_audience() -> None:
    issuer = TokenIssuer(
        signing_key=keys.generate(), issuer=ISSUER, audience="https://other/gw", ttl_seconds=60
    )
    issued = issuer.issue(subject="user:1", org="o", project="p", scopes=[])
    # A verifier expecting AUDIENCE rejects a token minted for a different audience.
    verifier = TokenIssuer(
        signing_key=issuer._key, issuer=ISSUER, audience=AUDIENCE, ttl_seconds=60
    )
    with pytest.raises(jwt.InvalidAudienceError):
        verifier.decode(issued.token)
