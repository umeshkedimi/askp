"""Security primitives for ASKP: signing keys and Access Token issuance.

This package implements the cryptographic core of the **Issuer** role (spec §4, §7.1): it mints
short-lived, EdDSA-signed JWT Access Tokens and verifies them. Keeping it isolated from the web
layer (``askp.api``) means the same code can be reused by the Gateway and by tests without
dragging in FastAPI.
"""
