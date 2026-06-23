"""Tests for envelope encryption (askp.security.encryption)."""

import base64

import pytest
from cryptography.exceptions import InvalidTag

from askp.security.encryption import Cipher, InvalidBlobError, generate_kek

AAD = "org_acme:openai"
SECRET = "sk-super-secret-provider-key"


def _cipher() -> Cipher:
    return Cipher(kek=base64.b64decode(generate_kek()))


def test_round_trip() -> None:
    cipher = _cipher()
    blob = cipher.encrypt(SECRET, aad=AAD)
    assert cipher.decrypt(blob, aad=AAD) == SECRET


def test_ciphertext_is_not_plaintext_and_is_nondeterministic() -> None:
    cipher = _cipher()
    blob1 = cipher.encrypt(SECRET, aad=AAD)
    blob2 = cipher.encrypt(SECRET, aad=AAD)
    assert SECRET not in blob1
    # Fresh DEK + nonce each time => same secret encrypts to different blobs.
    assert blob1 != blob2


def test_wrong_aad_fails() -> None:
    # A ciphertext bound to one org/provider cannot be decrypted under another (INV-4).
    cipher = _cipher()
    blob = cipher.encrypt(SECRET, aad=AAD)
    with pytest.raises(InvalidTag):
        cipher.decrypt(blob, aad="org_evil:openai")


def test_wrong_kek_fails() -> None:
    blob = _cipher().encrypt(SECRET, aad=AAD)
    with pytest.raises(InvalidTag):
        _cipher().decrypt(blob, aad=AAD)


def test_tampered_ciphertext_fails() -> None:
    cipher = _cipher()
    blob = cipher.encrypt(SECRET, aad=AAD)
    # Flip a character in the final (ciphertext) segment.
    parts = blob.split(".")
    parts[-1] = ("A" if parts[-1][0] != "A" else "B") + parts[-1][1:]
    with pytest.raises(InvalidTag):
        cipher.decrypt(".".join(parts), aad=AAD)


def test_malformed_blob_raises() -> None:
    with pytest.raises(InvalidBlobError):
        _cipher().decrypt("not-a-valid-blob", aad=AAD)


def test_kek_must_be_32_bytes() -> None:
    with pytest.raises(ValueError, match="KEK must be 32 bytes"):
        Cipher(kek=b"too-short")


def test_from_settings_requires_kek_in_production() -> None:
    with pytest.raises(RuntimeError, match="required in production"):
        Cipher.from_settings(vault_kek=None, is_production=True)


def test_from_settings_generates_ephemeral_in_dev() -> None:
    cipher = Cipher.from_settings(vault_kek=None, is_production=False)
    assert len(cipher.kek) == 32
