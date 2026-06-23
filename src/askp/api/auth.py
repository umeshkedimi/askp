"""Admin authentication for the control-plane endpoints.

The admin and token-issuance APIs are gated by a single bearer key from configuration
(``ASKP_ADMIN_API_KEY``). This is a deliberate placeholder for real principal authentication
(API key / client-credentials / OIDC), which is a later batch — but it fails *closed*: if no key
is configured the endpoints return 503, never an open door.

Used as a FastAPI dependency: ``dependencies=[Depends(require_admin)]`` on a router or route.
"""

from __future__ import annotations

import hmac

from fastapi import HTTPException, Request, status


def require_admin(request: Request) -> None:
    """Authorize an admin request, or raise the appropriate HTTP error.

    503 if the admin API is not configured; 401 if the bearer key is missing or wrong. The key is
    compared with ``hmac.compare_digest`` to avoid leaking length/contents through timing.
    """

    configured: str | None = request.app.state.settings.admin_api_key
    if not configured:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="admin API is not configured",
        )

    authorization = request.headers.get("authorization", "")
    presented = (
        authorization[len("bearer ") :].strip()
        if authorization[:7].lower() == "bearer "
        else ""
    )
    if not presented or not hmac.compare_digest(presented, configured):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="invalid admin credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
