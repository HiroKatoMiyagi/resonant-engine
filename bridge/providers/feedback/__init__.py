"""Feedback bridge providers."""

from .yuno_feedback_bridge import YunoFeedbackBridge
from .mock_feedback_bridge import MockFeedbackBridge

__all__ = [
    "YunoFeedbackBridge",
    "MockFeedbackBridge",
]
