"""Structured logging for ASKP, built on `structlog`.

Why structured logging? ASKP is security infrastructure — every request needs to be
attributable (spec invariant INV-6) and auditable. Structured logs emit machine-parseable
key/value events (JSON in production) instead of free-text strings, so fields like ``org``,
``project``, ``jti``, and ``request_id`` are first-class and queryable in your log pipeline.

Security note (spec §9 S-6): we MUST NOT log provider credentials or full access tokens. Keep
that in mind whenever you add fields to a log event.
"""

from __future__ import annotations

import logging
from typing import cast

import structlog

from askp.config import Settings


def configure_logging(settings: Settings) -> None:
    """Configure structlog + the stdlib logging bridge for the whole process.

    Call this once at startup. In development we render colorized, human-friendly console logs;
    in staging/production we render JSON lines suitable for ingestion by Loki/ELK/etc.
    """

    log_level = getattr(logging, settings.log_level.value.upper())

    shared_processors: list[structlog.typing.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
    ]

    renderer: structlog.typing.Processor = (
        structlog.processors.JSONRenderer()
        if settings.use_json_logs
        else structlog.dev.ConsoleRenderer()
    )

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Return a bound logger. Pass ``__name__`` from the calling module."""

    return cast(structlog.stdlib.BoundLogger, structlog.get_logger(name))
