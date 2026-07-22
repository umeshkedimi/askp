from collections.abc import Awaitable, Callable

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(tags=["health"])

# A readiness check is an async callable that raises on failure. Increment 1 registers
# Postgres/Redis checks here (`app.state.readiness_checks["postgres"] = ...`); Increment 0
# ships the mechanism with an empty registry so `/ready` is meaningful from day one without
# yet depending on anything.
ReadinessCheck = Callable[[], Awaitable[None]]


@router.get("/health")
async def health() -> dict[str, str]:
    """Liveness: no dependencies. A dependency outage must never fail this."""
    return {"status": "ok"}


@router.get("/ready")
async def ready(request: Request) -> JSONResponse:
    """Readiness: runs every registered check, fails closed on the first error."""
    checks: dict[str, ReadinessCheck] = request.app.state.readiness_checks
    results: dict[str, str] = {}
    all_ok = True

    for name, check in checks.items():
        try:
            await check()
        except Exception as exc:  # noqa: BLE001 - a checker failure must never propagate as a 500
            all_ok = False
            results[name] = f"error: {exc}"
        else:
            results[name] = "ok"

    status_code = 200 if all_ok else 503
    return JSONResponse(
        status_code=status_code,
        content={"status": "ready" if all_ok else "not_ready", "checks": results},
    )
