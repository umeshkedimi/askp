"""ASKP Gateway error responses (spec §8).

Errors are raised as :class:`GatewayError` from anywhere in the pipeline and turned into the
standard JSON body — ``{error, error_description, request_id}`` — by :func:`gateway_error_handler`,
registered on the app. The ``error`` codes are a **stable vocabulary** (§8): we use only the
spec's codes for the meanings it defines, plus two narrowly-scoped request-shape codes
(``invalid_request``, ``unsupported_operation``) the spec leaves to implementations.
"""

from __future__ import annotations

import uuid

from starlette.requests import Request
from starlette.responses import JSONResponse


class GatewayError(Exception):
    """A pipeline rejection carrying its §8 code, HTTP status, and a human description."""

    def __init__(self, *, code: str, status_code: int, description: str) -> None:
        super().__init__(f"{code}: {description}")
        self.code = code
        self.status_code = status_code
        self.description = description


# --- §8 vocabulary used in this increment ------------------------------------------------------


def invalid_token(description: str = "Missing or unverifiable Access Token") -> GatewayError:
    return GatewayError(code="invalid_token", status_code=401, description=description)


def token_revoked(description: str = "Access Token has been revoked") -> GatewayError:
    return GatewayError(code="token_revoked", status_code=401, description=description)


def insufficient_scope(description: str) -> GatewayError:
    return GatewayError(code="insufficient_scope", status_code=403, description=description)


def tenant_isolation(description: str) -> GatewayError:
    return GatewayError(code="tenant_isolation", status_code=403, description=description)


def provider_unavailable(description: str) -> GatewayError:
    return GatewayError(code="provider_unavailable", status_code=503, description=description)


# --- Implementation-defined request-shape codes (not repurposing §8 meanings) ------------------


def invalid_request(description: str) -> GatewayError:
    return GatewayError(code="invalid_request", status_code=400, description=description)


def unsupported_operation(description: str) -> GatewayError:
    return GatewayError(code="unsupported_operation", status_code=404, description=description)


async def gateway_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Render a GatewayError as the standard ASKP error body.

    Typed as ``Exception`` to match Starlette's handler signature; in practice it only receives
    GatewayError (it is registered for that type).
    """

    assert isinstance(exc, GatewayError)
    request_id = getattr(request.state, "request_id", None) or f"req_{uuid.uuid4().hex}"
    headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
    return JSONResponse(
        {"error": exc.code, "error_description": exc.description, "request_id": request_id},
        status_code=exc.status_code,
        headers=headers,
    )
