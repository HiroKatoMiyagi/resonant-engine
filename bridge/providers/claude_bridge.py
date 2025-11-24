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
        model: str = "claude-sonnet-4-5-20250929",
        client=None,
    ) -> None:
        warnings.warn(
            "ClaudeBridge is deprecated; use KanaAIBridge instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(api_key=api_key, model=model, client=client)
