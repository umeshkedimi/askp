"""Centralized configuration for ASKP.

We use :class:`pydantic_settings.BaseSettings`, which loads configuration from environment
variables (and an optional ``.env`` file) and validates it with Pydantic. This is the
"12-factor" approach: configuration lives in the environment, not in code, so the same image
runs unchanged across dev/staging/prod.

Every setting can be overridden with an ``ASKP_``-prefixed environment variable, e.g.
``ASKP_LOG_LEVEL=debug`` or ``ASKP_PORT=9000``.
"""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    """Deployment environment. Influences defaults like log formatting."""

    development = "development"
    staging = "staging"
    production = "production"


class LogLevel(StrEnum):
    debug = "debug"
    info = "info"
    warning = "warning"
    error = "error"


class Settings(BaseSettings):
    """Application settings, loaded once and reused (see :func:`get_settings`)."""

    model_config = SettingsConfigDict(
        env_prefix="ASKP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Service identity ---
    app_name: str = "askp"
    environment: Environment = Environment.development

    # --- HTTP server ---
    host: str = "127.0.0.1"
    port: int = 8000

    # --- Observability ---
    log_level: LogLevel = LogLevel.info
    # Pretty, colorized console logs in dev; structured JSON everywhere else. ``None`` means
    # "decide from the environment" (see the validator below).
    log_json: bool | None = None

    # --- Datastores (used from Increment 1 onward; declared now so config is stable) ---
    database_url: str = Field(
        default="postgresql+asyncpg://askp:askp@localhost:5432/askp",
        description="Async SQLAlchemy DSN for PostgreSQL.",
    )
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL (revocation list, rate-limit + budget counters).",
    )

    @property
    def is_production(self) -> bool:
        return self.environment == Environment.production

    @property
    def use_json_logs(self) -> bool:
        """Resolve the effective log format: explicit override, else JSON unless development."""
        if self.log_json is not None:
            return self.log_json
        return self.environment != Environment.development


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings singleton.

    ``lru_cache`` means the environment is read and validated exactly once per process. In tests
    you can clear it with ``get_settings.cache_clear()`` to load a different configuration.
    """

    return Settings()
