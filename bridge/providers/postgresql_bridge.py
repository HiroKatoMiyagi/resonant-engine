"""Backward compatibility alias for :class:`PostgresDataBridge`."""

from __future__ import annotations

import warnings
from typing import Optional

from bridge.providers.data.postgres_data_bridge import PostgresDataBridge


class PostgreSQLBridge(PostgresDataBridge):
    """Deprecated alias maintained for legacy imports."""

    def __init__(
        self,
        dsn: Optional[str] = None,
        min_size: int = 1,
        max_size: int = 10,
    ) -> None:
        warnings.warn(
            "PostgreSQLBridge is deprecated; use PostgresDataBridge instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(dsn=dsn, min_size=min_size, max_size=max_size)
