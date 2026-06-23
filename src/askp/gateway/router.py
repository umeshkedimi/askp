"""The Gateway proxy route — the §6.3 validation pipeline plus transparent passthrough.

One route handles every provider call: ``POST /v1/providers/{provider}/{native_path}`` (§6.1).
It runs the normative pipeline in order, stopping at the first failure (§6.3), and only resolves
the Provider Credential after pre-flight passes (steps 1–8 are pre-flight; INV-1/INV-2/INV-3):

    1–2. verify the JWS + standard claims   (TokenIssuer.decode)
    3.   revocation check                    (RevocationList.is_revoked)
    4.   resolve operation from path + body  (resolve_operation)
    5.   scope authorization (default deny)  (authorize)
    9.   resolve credential, within org      (CredentialResolver.resolve, §6.4)
    10.  proxy, streaming the response        (httpx, SSE-safe)

Steps 6–8 (policy re-check, rate limit, budget) and step 11 (usage/audit records) are later
increments; their slots are marked below so the order stays visible.
"""

from __future__ import annotations

import json

import httpx
import jwt
from starlette.background import BackgroundTask
from starlette.datastructures import Headers
from starlette.requests import Request
from starlette.responses import StreamingResponse

from askp.gateway import errors
from askp.gateway.credentials import CredentialResolver
from askp.gateway.providers import (
    UnknownProviderError,
    UnsupportedOperationError,
    resolve_operation,
)
from askp.security.revocation import RevocationList
from askp.security.scopes import authorize
from askp.security.tokens import TokenIssuer

# Headers we must not copy from the client request to the upstream Provider. We strip the
# client's credential (we substitute the provider's), plus connection-management headers httpx
# will set correctly itself.
_DROP_FROM_REQUEST = {"host", "authorization", "x-api-key", "content-length", "connection"}

# Headers we must not copy back from the upstream response. We decode the body (aiter_bytes), so
# content-encoding/content-length no longer apply, and the framing headers are Starlette's job.
_DROP_FROM_RESPONSE = {"content-encoding", "content-length", "transfer-encoding", "connection"}


async def proxy(request: Request) -> StreamingResponse:
    provider = request.path_params["provider"]
    native_path = request.path_params["native_path"]

    issuer: TokenIssuer = request.app.state.token_issuer
    revocations: RevocationList = request.app.state.revocations
    credentials: CredentialResolver = request.app.state.credentials
    http: httpx.AsyncClient = request.app.state.http

    # Steps 1–2 (§6.2, §6.3): present and verify the Access Token.
    token = _extract_token(request)
    try:
        claims = issuer.decode(token)
    except jwt.PyJWTError as exc:
        raise errors.invalid_token(str(exc)) from exc

    # Step 3: revocation (INV-5).
    if await revocations.is_revoked(jti=claims.jti, tf=claims.tf):
        raise errors.token_revoked()

    # Step 4: resolve the operation triple from the path and request body.
    body = await request.body()
    model = _model_from_body(body)
    try:
        spec, operation = resolve_operation(provider, native_path, model)
    except UnknownProviderError as exc:
        raise errors.unsupported_operation(f"unknown provider {provider!r}") from exc
    except UnsupportedOperationError as exc:
        raise errors.unsupported_operation(f"no capability for {provider}:{native_path}") from exc

    # Step 5: scope authorization (§5.2, default deny §5.3).
    if not authorize(claims.scopes, operation):
        raise errors.insufficient_scope(
            "Token does not authorize "
            f"provider:{operation.provider}:model:{operation.model}:{operation.capability}"
        )

    # Steps 6–8 (policy re-check, rate limit, budget): later increments.

    # Step 9: resolve the Provider Credential, strictly within the token's org (§6.4, INV-1).
    credential = await credentials.resolve(org=claims.org, provider=provider)
    if credential is None:
        raise errors.provider_unavailable(f"no credential for provider {provider!r}")

    # Step 10: transparent passthrough, streaming the response so SSE is not buffered (§6.6).
    upstream_url = f"{spec.base_url}/{native_path.lstrip('/')}"
    upstream_headers = _forward_request_headers(request.headers)
    upstream_headers.update(spec.auth(credential))

    upstream_request = http.build_request(
        "POST",
        upstream_url,
        content=body,
        headers=upstream_headers,
        params=list(request.query_params.multi_items()),
    )
    try:
        upstream_response = await http.send(upstream_request, stream=True)
    except httpx.RequestError as exc:
        raise errors.provider_unavailable(f"upstream request failed: {exc}") from exc

    # Step 11 (usage + audit records): later increment.
    return StreamingResponse(
        upstream_response.aiter_bytes(),
        status_code=upstream_response.status_code,
        headers=_forward_response_headers(upstream_response.headers),
        background=BackgroundTask(upstream_response.aclose),
    )


def _extract_token(request: Request) -> str:
    """Pull the Access Token from the Authorization header, or a provider key field (§6.2)."""
    authorization = request.headers.get("authorization")
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[len("bearer ") :].strip()
    # Compatibility mode: a Provider SDK that only sends an API key carries the askp_at_ token in
    # that field instead.
    api_key = request.headers.get("x-api-key")
    if api_key:
        return api_key
    raise errors.invalid_token("no bearer token presented")


def _model_from_body(body: bytes) -> str:
    """Extract the required ``model`` field from a JSON request body."""
    try:
        payload = json.loads(body)
    except (ValueError, TypeError) as exc:
        raise errors.invalid_request("request body is not valid JSON") from exc
    model = payload.get("model") if isinstance(payload, dict) else None
    if not isinstance(model, str) or not model:
        raise errors.invalid_request("request body must include a 'model' string")
    return model


def _forward_request_headers(headers: Headers) -> dict[str, str]:
    return {k: v for k, v in headers.items() if k.lower() not in _DROP_FROM_REQUEST}


def _forward_response_headers(headers: httpx.Headers) -> dict[str, str]:
    return {k: v for k, v in headers.items() if k.lower() not in _DROP_FROM_RESPONSE}
