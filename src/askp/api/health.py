"""Health and readiness endpoints.

These are operational endpoints used by humans, load balancers, and Kubernetes probes:

- ``/health``  — liveness: "is the process up?" Always cheap, no dependencies.
- ``/ready``   — readiness: "can it serve traffic?" Later this will check Postgres/Redis.

Keeping liveness dependency-free is deliberate: a liveness probe that fails when the database
blips would cause Kubernetes to kill an otherwise-healthy process. Readiness is where dependency
checks belong.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from askp import __version__

router = APIRouter(tags=["operations"])


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


@router.get("/health", response_model=HealthResponse, summary="Liveness probe")
async def health() -> HealthResponse:
    """Return ``ok`` if the process is running. No external dependencies are checked."""

    return HealthResponse(status="ok", service="askp", version=__version__)


@router.get("/ready", response_model=HealthResponse, summary="Readiness probe")
async def ready() -> HealthResponse:
    """Return ``ready`` if the service can serve traffic.

    For Increment 0 this mirrors liveness. From Increment 1 it will verify connectivity to
    PostgreSQL and Redis before reporting ready.
    """

    return HealthResponse(status="ready", service="askp", version=__version__)
