"""Module entrypoint for ``python -m bridge.etl``."""

from __future__ import annotations

from .cli import main


if __name__ == "__main__":  # pragma: no cover - CLI guard
    main()
