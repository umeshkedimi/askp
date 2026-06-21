"""Health and readiness endpoints.

These are operational endpoints used by humans, load balancers, and Kubernetes probes:

- ``/health`` — liveness: "is the process up?" Always cheap, no dependencies.
- ``/ready``  — readiness: "can it serve traffic?" Checks PostgreSQL and Redis.

Keeping liveness dependency-free is deliberate: a liveness probe that fails when the database
blips would cause Kubernetes to kill an otherwise-healthy process. Readiness is where dependency
checks belong — a not-ready pod is removed from the load balancer but not killed.
"""

from __future__ import annotations

from fastapi import APIRouter, Request, Response, status
from pydantic import BaseModel

from askp import __version__
from askp.db import Database
from askp.redis import check_redis

router = APIRouter(tags=["operations"])


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class ReadyResponse(BaseModel):
    status: str
    service: str
    version: str
    checks: dict[str, bool]


@router.get("/health", response_model=HealthResponse, summary="Liveness probe")
async def health() -> HealthResponse:
    """Return ``ok`` if the process is running. No external dependencies are checked."""

    return HealthResponse(status="ok", service="askp", version=__version__)


@router.get("/ready", response_model=ReadyResponse, summary="Readiness probe")
async def ready(request: Request, response: Response) -> ReadyResponse:
    """Report readiness based on connectivity to PostgreSQL and Redis.

    Returns HTTP 200 when every dependency is reachable, otherwise HTTP 503 with a per-check
    breakdown so operators can see exactly what is down.
    """

    db: Database = request.app.state.db
    checks = {
        "database": await db.check(),
        "redis": await check_redis(request.app.state.redis),
    }
    all_ok = all(checks.values())
    response.status_code = status.HTTP_200_OK if all_ok else status.HTTP_503_SERVICE_UNAVAILABLE

    return ReadyResponse(
        status="ready" if all_ok else "degraded",
        service="askp",
        version=__version__,
        checks=checks,
    )
