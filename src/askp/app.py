"""FastAPI application factory.

We build the app inside a function (``create_app``) rather than as a module-level global. This
"app factory" pattern is the FastAPI/Flask idiom because it:

- makes tests hermetic — each test can construct a fresh app with its own settings;
- defers expensive setup (DB pools, etc.) until an app is actually created;
- lets a single codebase assemble different role-specific apps later (Issuer / Gateway /
  Admin), which the protocol explicitly allows (spec §2.1 — roles MAY be co-located).

The ``lifespan`` async context manager is where startup/shutdown work goes (opening and closing
connection pools from Increment 1 onward).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from askp import __version__
from askp.api import health
from askp.config import Settings, get_settings
from askp.logging import configure_logging, get_logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup/shutdown hooks. Everything before ``yield`` runs on startup, after on shutdown."""

    settings: Settings = app.state.settings
    log = get_logger(__name__)
    log.info(
        "askp.startup",
        environment=settings.environment.value,
        version=__version__,
    )
    # Increment 1: open the database engine and Redis pool here.
    yield
    # Increment 1: dispose of the database engine and Redis pool here.
    log.info("askp.shutdown")


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build and return a configured ASKP FastAPI application."""

    settings = settings or get_settings()
    configure_logging(settings)

    app = FastAPI(
        title="ASKP — AI Secure Key Protocol",
        version=__version__,
        summary="OAuth for AI provider access.",
        description=(
            "Reference implementation of the askp/v1 protocol. "
            "See https://github.com/umeshkedimi/askp for the specification."
        ),
        lifespan=lifespan,
    )
    # Stash settings on app.state so routers and dependencies can reach them.
    app.state.settings = settings

    app.include_router(health.router)

    return app
