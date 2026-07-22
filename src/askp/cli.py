import argparse
import sys

import uvicorn

from askp.config import get_settings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="askp")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("serve", help="Run the ASKP HTTP server")

    args = parser.parse_args(argv)

    if args.command == "serve":
        return _serve()

    parser.print_help()
    return 1


def _serve() -> int:
    settings = get_settings()
    uvicorn.run(
        "askp.app:create_app",
        factory=True,
        host=settings.host,
        port=settings.port,
        # askp.observability.logging owns log configuration; don't let uvicorn
        # install its own handlers on top of it.
        log_config=None,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
