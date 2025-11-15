"""Backward compatibility aliases for mock providers."""

from __future__ import annotations

import warnings

from bridge.providers.ai.mock_ai_bridge import MockAIBridge as _MockAIBridge
from bridge.providers.data.mock_data_bridge import MockDataBridge as _MockDataBridge
from bridge.providers.feedback.mock_feedback_bridge import (
    MockFeedbackBridge as _MockFeedbackBridge,
)


class MockDataBridge(_MockDataBridge):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "bridge.providers.mock_bridge.MockDataBridge is deprecated; import from "
            "bridge.providers.data instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)


class MockAIBridge(_MockAIBridge):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "bridge.providers.mock_bridge.MockAIBridge is deprecated; import from "
            "bridge.providers.ai instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)


class MockFeedbackBridge(_MockFeedbackBridge):
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "bridge.providers.mock_bridge.MockFeedbackBridge is deprecated; import from "
            "bridge.providers.feedback instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)
