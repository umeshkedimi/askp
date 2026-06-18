"""Command-line entrypoint for ASKP.

Exposed as the ``askp`` command (see ``[project.scripts]`` in ``pyproject.toml``). For now it
runs the HTTP server; subcommands (e.g. selecting a role, running migrations) arrive in later
increments.

Run it with:

    uv run askp serve
"""

from __future__ import annotations

import argparse

import uvicorn

from askp.config import get_settings


def main() -> None:
    parser = argparse.ArgumentParser(prog="askp", description="ASKP — AI Secure Key Protocol")
    sub = parser.add_subparsers(dest="command")

    serve = sub.add_parser("serve", help="Run the ASKP HTTP server")
    serve.add_argument("--host", default=None, help="Bind host (overrides ASKP_HOST)")
    serve.add_argument("--port", type=int, default=None, help="Bind port (overrides ASKP_PORT)")
    serve.add_argument("--reload", action="store_true", help="Auto-reload on code changes (dev)")

    args = parser.parse_args()

    if args.command in (None, "serve"):
        settings = get_settings()
        uvicorn.run(
            "askp.app:create_app",
            factory=True,
            host=getattr(args, "host", None) or settings.host,
            port=getattr(args, "port", None) or settings.port,
            reload=getattr(args, "reload", False),
            log_config=None,  # we configure logging ourselves via structlog
        )
    else:  # pragma: no cover - argparse handles unknown commands
        parser.print_help()


if __name__ == "__main__":
    main()
