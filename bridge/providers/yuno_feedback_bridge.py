"""Backward compatibility alias for :class:`YunoFeedbackBridge`."""

from __future__ import annotations

import warnings
from typing import Optional

from bridge.providers.feedback.yuno_feedback_bridge import YunoFeedbackBridge as _YunoFeedbackBridge


class YunoFeedbackBridge(_YunoFeedbackBridge):  # type: ignore[misc]
    """Deprecated alias maintained for legacy imports."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-5-preview",
        client=None,
    ) -> None:
        warnings.warn(
            "bridge.providers.yuno_feedback_bridge.YunoFeedbackBridge is deprecated; import from "
            "bridge.providers.feedback instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(api_key=api_key, model=model, client=client)
