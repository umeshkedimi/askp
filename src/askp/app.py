from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from askp import __version__
from askp.api import health
from askp.api.health import ReadinessCheck
from askp.config import Settings, get_settings
from askp.observability import configure_logging

logger = structlog.get_logger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the ASKP FastAPI app from a settings object.

    An explicit factory (rather than a module-level `app = FastAPI()`) keeps tests
    hermetic — each test can construct its own app with its own `Settings` override —
    and leaves room for a future increment to assemble differently-scoped
    Issuer/Gateway/Admin processes from the same codebase, as the architecture doc allows.
    """
    settings = settings or get_settings()
    configure_logging(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        logger.info("askp.startup", environment=settings.environment.value)
        yield
        logger.info("askp.shutdown")

    app = FastAPI(title="ASKP", version=__version__, lifespan=lifespan)
    app.state.settings = settings
    readiness_checks: dict[str, ReadinessCheck] = {}
    app.state.readiness_checks = readiness_checks

    app.include_router(health.router)

    return app
