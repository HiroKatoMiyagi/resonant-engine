"""Mock AI bridge for predictable unit tests."""

from __future__ import annotations

from typing import Any, Dict

from bridge.core.ai_bridge import AIBridge


class MockAIBridge(AIBridge):
    """Return canned responses instead of calling a real provider."""

    def __init__(self, response: Dict[str, Any] | None = None) -> None:
        self._response = response or {
            "summary": "Mock analysis",
            "confidence": 0.75,
        }

    async def process_intent(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "intent_type": intent.get("type"),
            "analysis": self._response,
        }
