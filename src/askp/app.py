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

import httpx
from fastapi import FastAPI

from askp import __version__
from askp.api import admin, health, tokens
from askp.config import Settings, get_settings
from askp.db import Database
from askp.gateway import errors as gateway_errors
from askp.gateway.router import proxy
from askp.logging import configure_logging, get_logger
from askp.redis import create_redis
from askp.security.encryption import Cipher
from askp.security.revocation import RevocationList
from askp.security.tokens import TokenIssuer
from askp.vault import Vault


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup/shutdown hooks. Everything before ``yield`` runs on startup, after on shutdown."""

    settings: Settings = app.state.settings
    log = get_logger(__name__)

    # Construct datastore clients. Both are lazy — they don't connect here — so startup never
    # fails just because Postgres/Redis aren't up yet; the readiness probe reports the truth.
    app.state.db = Database(settings.database_url)
    app.state.redis = create_redis(settings.redis_url)

    # Gateway dependencies. The TokenIssuer holds the signing key (verify side on the Gateway);
    # the RevocationList shares the Redis client; the credential resolver is the Vault stand-in;
    # the httpx client is reused across requests for connection pooling to upstream Providers.
    app.state.token_issuer = TokenIssuer.from_settings(settings)
    app.state.revocations = RevocationList(app.state.redis)
    cipher = Cipher.from_settings(
        vault_kek=settings.vault_kek, is_production=settings.is_production
    )
    vault = Vault(session_factory=app.state.db.session_factory, cipher=cipher)
    app.state.vault = vault  # concrete Vault for the admin API (put/delete)
    app.state.credentials = vault  # CredentialResolver seam for the Gateway (resolve)
    app.state.http = httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=10.0))

    log.info("askp.startup", environment=settings.environment.value, version=__version__)

    yield

    await app.state.http.aclose()
    await app.state.db.dispose()
    await app.state.redis.aclose()
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
    app.include_router(tokens.router)
    app.include_router(admin.router)

    # The Gateway proxy is a raw passthrough route (not in the OpenAPI schema): it forwards
    # provider-native request shapes under a provider-scoped path (spec §6.1).
    app.add_route("/v1/providers/{provider}/{native_path:path}", proxy, methods=["POST"])
    app.add_exception_handler(gateway_errors.GatewayError, gateway_errors.gateway_error_handler)

    return app
