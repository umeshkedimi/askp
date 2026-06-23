"""Token issuance endpoint (spec §7.1, exchange steps 1-3).

``POST /v1/tokens`` is the Issuer's front door: it mints a scoped, short-lived Access Token. In a
full deployment the Issuer authenticates a Principal and evaluates its Access Policy to decide the
granted scopes; here the request states the subject/org/project/scopes directly and is gated by
the admin key (principal auth + policy are later batches). The granted ``scopes`` are trusted as
given — the Gateway remains the final authority at request time (§4.2).

The response uses OAuth-style fields (``access_token``, ``token_type``, ``expires_in``) so it is
familiar to anyone who has integrated an OAuth token endpoint.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from askp.api.auth import require_admin
from askp.security.tokens import TokenIssuer

router = APIRouter(prefix="/v1", tags=["tokens"])


class TokenRequest(BaseModel):
    subject: str = Field(description="Principal identifier, e.g. 'agent:6f2c' or 'user:42'.")
    org: str
    project: str
    scopes: list[str] = Field(default_factory=list)
    budget_refs: list[str] | None = None
    token_family: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    jti: str
    scopes: list[str]


@router.post("/tokens", response_model=TokenResponse, dependencies=[Depends(require_admin)])
async def issue_token(body: TokenRequest, request: Request) -> TokenResponse:
    issuer: TokenIssuer = request.app.state.token_issuer
    issued = issuer.issue(
        subject=body.subject,
        org=body.org,
        project=body.project,
        scopes=body.scopes,
        budget_refs=body.budget_refs,
        token_family=body.token_family,
    )
    expires_in = int((issued.claims.exp - issued.claims.iat).total_seconds())
    return TokenResponse(
        access_token=issued.token,
        expires_in=expires_in,
        jti=issued.jti,
        scopes=issued.claims.scopes,
    )
