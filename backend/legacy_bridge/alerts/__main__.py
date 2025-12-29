"""CLI entrypoint for running the AlertManager."""

from __future__ import annotations

import asyncio
import logging

from .manager import run_forever

logging.basicConfig(level=logging.INFO)


def main() -> None:
    try:
        asyncio.run(run_forever())
    except KeyboardInterrupt:  # pragma: no cover - CLI convenience
        logging.getLogger(__name__).info("Alert manager interrupted, exiting")


if __name__ == "__main__":  # pragma: no cover - CLI guard
    main()
