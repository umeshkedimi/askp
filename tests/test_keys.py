"""Tests for Ed25519 signing-key management (askp.security.keys)."""

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.rsa import generate_private_key

from askp.security import keys


def _to_pem(private_key: Ed25519PrivateKey) -> bytes:
    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )


def test_generate_produces_usable_key() -> None:
    key = keys.generate()
    assert key.algorithm == "EdDSA"
    assert key.kid  # non-empty identifier
    # The public half is derivable and is the verifying counterpart.
    assert isinstance(key.public_key.public_bytes_raw(), bytes)


def test_kid_is_deterministic_for_same_key(tmp_path) -> None:
    # A given key must always hash to the same kid, so a reload (or another instance) agrees.
    original = keys.generate()
    pem_file = tmp_path / "signing.pem"
    pem_file.write_bytes(_to_pem(original.private_key))

    reloaded = keys.load_pem(pem_file)
    assert reloaded.kid == original.kid


def test_load_pem_rejects_non_ed25519(tmp_path) -> None:
    # An RSA key in the PEM must fail loudly rather than silently mis-signing.
    rsa_pem = generate_private_key(public_exponent=65537, key_size=2048).private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pem_file = tmp_path / "rsa.pem"
    pem_file.write_bytes(rsa_pem)

    with pytest.raises(ValueError, match="not an Ed25519 private key"):
        keys.load_pem(pem_file)
