"""Backward compatibility wrapper for :class:`KanaAIBridge`."""

from __future__ import annotations

import warnings
from typing import Optional

from bridge.providers.ai.kana_ai_bridge import KanaAIBridge


class ClaudeBridge(KanaAIBridge):
    """Deprecated alias kept for existing imports."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
        client=None,
    ) -> None:
        warnings.warn(
            "ClaudeBridge is deprecated; use KanaAIBridge instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(api_key=api_key, model=model, client=client)
