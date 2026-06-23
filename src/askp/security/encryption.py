"""Envelope encryption for Provider Credentials (spec §7.4, invariant INV-1).

Provider Credentials must be stored encrypted at rest and decrypted only in-boundary at forward
time. We use **envelope encryption** with AES-256-GCM:

- A **KEK** (key-encryption key) is the master secret. It lives in configuration (or, in a real
  deployment, a KMS/HSM) and never directly encrypts a credential.
- Each credential is encrypted under its own freshly generated **DEK** (data-encryption key).
  The DEK is then *wrapped* (encrypted) by the KEK and stored next to the ciphertext.

Why bother with two layers? Rotating the KEK only re-wraps small DEKs instead of re-encrypting
every secret; the KEK can be held in an HSM that only ever does wrap/unwrap; and a single leaked
DEK exposes exactly one credential.

AES-GCM is an **AEAD** cipher: it provides confidentiality *and* integrity, and authenticates
extra "associated data" (AAD) without encrypting it. We bind ``AAD = "<org>:<provider>"`` into
both layers, so a stored ciphertext cannot be decrypted under any other org/provider — tenant
isolation enforced by the math, not just by a WHERE clause.
"""

from __future__ import annotations

import base64
import os
from dataclasses import dataclass

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Serialized-blob format tag. Bumping this lets us evolve the on-disk layout without ambiguity.
_FORMAT = "v1"
# GCM standard nonce size (96 bits). A fresh random nonce per encryption is required — never
# reuse a (key, nonce) pair with GCM.
_NONCE_LEN = 12
_KEK_LEN = 32  # AES-256


class InvalidBlobError(ValueError):
    """The stored ciphertext blob is malformed (wrong format tag or field count)."""


def _b64e(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64d(text: str) -> bytes:
    padding = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(text + padding)


def generate_kek() -> str:
    """Return a fresh, base64-encoded 32-byte KEK suitable for ``ASKP_VAULT_KEK``."""
    return base64.b64encode(AESGCM.generate_key(bit_length=256)).decode("ascii")


@dataclass(frozen=True)
class Cipher:
    """Encrypts/decrypts secrets under a master KEK using envelope encryption."""

    kek: bytes

    def __post_init__(self) -> None:
        if len(self.kek) != _KEK_LEN:
            raise ValueError(f"KEK must be {_KEK_LEN} bytes, got {len(self.kek)}")

    @classmethod
    def from_settings(cls, *, vault_kek: str | None, is_production: bool) -> Cipher:
        """Build a Cipher from configuration.

        Requires ``vault_kek`` in production; for dev/tests an ephemeral key is generated (so
        credentials cannot be decrypted after a restart — fine for local work, never for prod).
        """

        if vault_kek:
            return cls(kek=base64.b64decode(vault_kek))
        if is_production:
            raise RuntimeError("ASKP_VAULT_KEK is required in production")
        return cls(kek=AESGCM.generate_key(bit_length=256))

    def encrypt(self, plaintext: str, *, aad: str) -> str:
        """Encrypt ``plaintext``, returning a self-contained, base64 blob string.

        The blob carries everything needed to decrypt *given the KEK*: the wrapped DEK and both
        GCM nonces. It does not carry the AAD — the caller must supply the same AAD to decrypt.
        """

        aad_bytes = aad.encode("utf-8")

        dek = AESGCM.generate_key(bit_length=256)
        dek_nonce = os.urandom(_NONCE_LEN)
        ciphertext = AESGCM(dek).encrypt(dek_nonce, plaintext.encode("utf-8"), aad_bytes)

        kek_nonce = os.urandom(_NONCE_LEN)
        wrapped_dek = AESGCM(self.kek).encrypt(kek_nonce, dek, aad_bytes)

        return ".".join(
            [_FORMAT, _b64e(kek_nonce), _b64e(wrapped_dek), _b64e(dek_nonce), _b64e(ciphertext)]
        )

    def decrypt(self, blob: str, *, aad: str) -> str:
        """Reverse :meth:`encrypt`. Raises ``InvalidTag`` if the KEK or AAD is wrong, or if the
        blob has been tampered with; raises :class:`InvalidBlobError` on a malformed blob."""

        parts = blob.split(".")
        if len(parts) != 5 or parts[0] != _FORMAT:
            raise InvalidBlobError(blob[:16] + "…")
        _, kek_nonce_b64, wrapped_b64, dek_nonce_b64, ciphertext_b64 = parts
        aad_bytes = aad.encode("utf-8")

        dek = AESGCM(self.kek).decrypt(_b64d(kek_nonce_b64), _b64d(wrapped_b64), aad_bytes)
        plaintext = AESGCM(dek).decrypt(_b64d(dek_nonce_b64), _b64d(ciphertext_b64), aad_bytes)
        return plaintext.decode("utf-8")
