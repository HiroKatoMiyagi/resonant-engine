"""Kana (Anthropic Claude) AI bridge implementation."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

from anthropic import APIStatusError, AsyncAnthropic

from bridge.core.ai_bridge import AIBridge


class KanaAIBridge(AIBridge):
    """Wrap Anthropic Claude as the Kana intent processor."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
        client: Optional[AsyncAnthropic] = None,
    ) -> None:
        key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not key and client is None:
            raise ValueError("ANTHROPIC_API_KEY must be configured for KanaAIBridge")
        self._model = model
        self._client = client or AsyncAnthropic(api_key=key)

    async def process_intent(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        prompt = self._build_prompt(intent)
        try:
            response = await self._client.messages.create(  # type: ignore[attr-defined]
                model=self._model,
                max_tokens=1024,
                temperature=0.5,
                messages=[
                    {
                        "role": "system",
                        "content": "You are Kana, the external translator for Resonant Engine.",
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
            )
        except APIStatusError as exc:  # pragma: no cover - network failure path
            return {
                "status": "error",
                "reason": str(exc),
            }

        message = response.content[0]
        summary = getattr(message, "text", None) or str(message)
        return {
            "status": "ok",
            "model": self._model,
            "summary": summary,
        }

    @staticmethod
    def _build_prompt(intent: Dict[str, Any]) -> str:
        intent_type = intent.get("type", "unknown")
        payload = intent.get("payload", {})
        return (
            "# Intent Summary\n"
            f"Type: {intent_type}\n"
            "Describe the key considerations, potential risks, and immediate next actions.\n\n"
            "## Payload\n"
            f"{payload}"
        )
