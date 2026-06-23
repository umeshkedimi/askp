"""Ed25519 signing keys for ASKP Access Tokens.

The protocol (spec §4.1) requires the Issuer to sign Access Tokens with ``EdDSA`` (Ed25519) or
``RS256``, and to *prefer* EdDSA. We implement EdDSA: the keys are tiny (a 32-byte seed),
signing is fast and constant-time, and there are none of RSA's padding-mode footguns.

This module owns **key material only** — loading, generating, and identifying keys. It knows
nothing about JWT claims; that separation lets us rotate or swap keys without touching token
content (and vice versa). Token assembly lives in :mod:`askp.security.tokens`.
"""

from __future__ import annotations

import base64
import hashlib
from dataclasses import dataclass
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

# The JWS "alg" header value for Ed25519 signatures (RFC 8037). PyJWT understands this name and
# routes it to the cryptography backend.
ALGORITHM = "EdDSA"


@dataclass(frozen=True)
class SigningKey:
    """An Ed25519 key pair plus a stable key identifier (``kid``).

    Frozen (immutable) because a key's identity must never change underneath a token that was
    signed with it. We pass this object to the token Issuer, which uses ``private_key`` to sign
    and advertises ``kid`` in the JWT header so verifiers can select the right public key.
    """

    private_key: Ed25519PrivateKey
    kid: str

    @property
    def public_key(self) -> Ed25519PublicKey:
        """The verifying half of the pair (safe to publish, e.g. via a future JWKS endpoint)."""
        return self.private_key.public_key()

    @property
    def algorithm(self) -> str:
        return ALGORITHM


def _compute_kid(public_key: Ed25519PublicKey) -> str:
    """Derive a deterministic key id from the public key.

    We hash the raw 32-byte public key and take a short base64url prefix. "Deterministic" matters:
    the same key always yields the same ``kid``, so a restart (or a second instance loading the
    same PEM) agrees on the identifier without coordination.
    """

    raw = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    digest = hashlib.sha256(raw).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")[:16]


def generate() -> SigningKey:
    """Create a fresh, ephemeral Ed25519 signing key.

    Used in development and tests. **Never** rely on this in production: the key lives only in
    memory, so a restart invalidates every previously issued token and other instances can't
    verify what this one signed.
    """

    private_key = Ed25519PrivateKey.generate()
    return SigningKey(private_key=private_key, kid=_compute_kid(private_key.public_key()))


def load_pem(path: str | Path) -> SigningKey:
    """Load an Ed25519 private key from an unencrypted PEM file.

    Raises ``ValueError`` if the file does not contain an Ed25519 private key, so a misconfigured
    key fails loudly at startup rather than producing unverifiable tokens later.
    """

    pem_bytes = Path(path).read_bytes()
    key = serialization.load_pem_private_key(pem_bytes, password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise ValueError(f"{path!r} is not an Ed25519 private key (got {type(key).__name__})")
    return SigningKey(private_key=key, kid=_compute_kid(key.public_key()))
