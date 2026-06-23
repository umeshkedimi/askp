"""ASKP Access Token issuance and verification (spec §4, §7.1).

This is the Issuer's core: it assembles the claim set the protocol mandates, signs it as an
EdDSA JWT, and hands back a transport string prefixed with ``askp_at_``. It can also verify a
token — the same logic the Gateway will use on the hot path.

Design notes for learners:

- We pin the accepted algorithm to ``EdDSA`` at *decode* time. That single line is what enforces
  the spec's "MUST NOT accept alg: none" (and blocks the classic alg-confusion attack where a
  forged token claims a symmetric ``alg`` so the public key is used as an HMAC secret).
- ``issue()`` accepts an injectable ``now`` so tests can mint already-expired tokens without a
  clock-mocking dependency.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt
from pydantic import BaseModel

from askp.config import Settings
from askp.security import keys
from askp.security.keys import SigningKey

# Transport prefix (spec §4.1). It is metadata around the JWS, not part of the signed token, so
# we add it after signing and strip it before verifying.
TOKEN_PREFIX = "askp_at_"


class AccessTokenClaims(BaseModel):
    """A typed view of a decoded Access Token payload (spec §4.2).

    Every field below maps to a JWT claim of the same name. ``exp``/``iat``/``nbf`` arrive from
    PyJWT as Unix timestamps; Pydantic v2 coerces those integers into aware ``datetime`` objects
    for us.
    """

    iss: str
    aud: str
    sub: str
    exp: datetime
    iat: datetime
    jti: str
    org: str
    proj: str
    scopes: list[str]
    nbf: datetime | None = None
    bud: list[str] | None = None
    tf: str | None = None
    cnf: dict[str, str] | None = None


@dataclass(frozen=True)
class IssuedToken:
    """The result of minting a token: the transport string plus useful metadata.

    ``jti`` and ``expires_at`` are surfaced so the caller can record the token (e.g. for the
    revocation list and audit log) without re-decoding what it just signed.
    """

    token: str  # the askp_at_-prefixed transport string
    jti: str
    expires_at: datetime
    claims: AccessTokenClaims


class TokenIssuer:
    """Mints and verifies Access Tokens for one Issuer identity + signing key."""

    def __init__(
        self,
        *,
        signing_key: SigningKey,
        issuer: str,
        audience: str,
        ttl_seconds: int,
    ) -> None:
        self._key = signing_key
        self._issuer = issuer
        self._audience = audience
        self._ttl = timedelta(seconds=ttl_seconds)

    @classmethod
    def from_settings(cls, settings: Settings) -> TokenIssuer:
        """Build an Issuer from app settings.

        This is where key material (askp.security.keys) and configuration meet: load the signing
        key from the configured PEM, or generate an ephemeral one for dev/tests.
        """

        if settings.signing_key_path:
            signing_key = keys.load_pem(settings.signing_key_path)
        else:
            signing_key = keys.generate()
        return cls(
            signing_key=signing_key,
            issuer=settings.issuer,
            audience=settings.gateway_audience,
            ttl_seconds=settings.access_token_ttl_seconds,
        )

    @property
    def kid(self) -> str:
        return self._key.kid

    def issue(
        self,
        *,
        subject: str,
        org: str,
        project: str,
        scopes: list[str],
        budget_refs: list[str] | None = None,
        token_family: str | None = None,
        now: datetime | None = None,
    ) -> IssuedToken:
        """Mint a signed Access Token for a Principal.

        ``scopes`` are the *granted* scopes; per spec §4.2 they MUST already be a subset of what
        the Principal's policy allows. Policy evaluation is a later increment — here we trust the
        caller and focus on producing a correct, signed token.
        """

        issued_at = now or datetime.now(UTC)
        expires_at = issued_at + self._ttl
        jti = f"at_{uuid.uuid4().hex}"

        # Reserved JWT claims (iss/aud/sub/exp/iat/jti) plus ASKP's custom claims.
        payload: dict[str, object] = {
            "iss": self._issuer,
            "aud": self._audience,
            "sub": subject,
            "exp": expires_at,
            "iat": issued_at,
            "jti": jti,
            "org": org,
            "proj": project,
            "scopes": scopes,
        }
        if budget_refs:
            payload["bud"] = budget_refs
        if token_family:
            payload["tf"] = token_family

        raw = jwt.encode(
            payload,
            self._key.private_key,
            algorithm=self._key.algorithm,
            headers={"kid": self._key.kid},
        )

        # Build the typed claims directly from the payload we just signed. We must NOT verify the
        # token here to do it: issuance shouldn't depend on verification succeeding (e.g. a
        # deliberately back-dated token would fail an expiry check during minting).
        claims = AccessTokenClaims.model_validate(payload)
        return IssuedToken(
            token=TOKEN_PREFIX + raw,
            jti=jti,
            expires_at=expires_at,
            claims=claims,
        )

    def decode(self, token: str, *, verify_aud: bool = True) -> AccessTokenClaims:
        """Verify a token's signature and standard claims, returning the typed claim set.

        Raises a ``jwt.PyJWTError`` subclass on any failure (bad signature, expired, wrong
        issuer/audience, forbidden algorithm). The caller decides how to translate that into an
        ASKP error response (spec §8).
        """

        raw = token.removeprefix(TOKEN_PREFIX)
        payload = jwt.decode(
            raw,
            self._key.public_key,
            algorithms=[keys.ALGORITHM],  # EdDSA only — never 'none' or a symmetric alg.
            issuer=self._issuer,
            audience=self._audience if verify_aud else None,
            options={
                "require": ["exp", "iat", "jti", "iss", "aud", "sub"],
                "verify_aud": verify_aud,
            },
        )
        return AccessTokenClaims.model_validate(payload)
