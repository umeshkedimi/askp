"""Admin control-plane endpoints (spec §7.4 credential lifecycle).

These manage the encrypted Vault. The whole router is gated by :func:`require_admin`.

Write-only by design: there is a ``PUT`` (write or rotate) and a ``DELETE``, but **no GET** —
§7.4 requires that Provider Credentials never be readable back through any API. The only read
path is the Gateway's in-boundary ``resolve`` at forward time.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel

from askp.api.auth import require_admin
from askp.vault import Vault

router = APIRouter(prefix="/v1/admin", tags=["admin"], dependencies=[Depends(require_admin)])


class CredentialUpsert(BaseModel):
    org: str
    secret: str


@router.put("/providers/{provider}/credential", status_code=status.HTTP_204_NO_CONTENT)
async def put_credential(provider: str, body: CredentialUpsert, request: Request) -> Response:
    """Write or rotate the credential for ``(org, provider)``. Idempotent on the key."""
    vault: Vault = request.app.state.vault
    await vault.put(org=body.org, provider=provider, secret=body.secret)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/providers/{provider}/credential", status_code=status.HTTP_204_NO_CONTENT)
async def delete_credential(provider: str, org: str, request: Request) -> Response:
    """Delete the credential for ``(org, provider)`` (``org`` is a query parameter)."""
    vault: Vault = request.app.state.vault
    deleted = await vault.delete(org=org, provider=provider)
    if not deleted:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="credential not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
