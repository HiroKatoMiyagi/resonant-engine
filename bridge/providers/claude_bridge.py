"""Anthropic Claude implementation of the AIBridge."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

from anthropic import AsyncAnthropic, APIStatusError

from bridge.core.ai_bridge import AIBridge


class ClaudeBridge(AIBridge):
    """Anthropic Claude用のAIBridge実装。"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
        client: Optional[AsyncAnthropic] = None,
    ) -> None:
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEYが指定されていません。")
        self.model = model
        self.client = client or AsyncAnthropic(api_key=self.api_key)

    async def call_ai(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> Optional[str]:
        request_model = model or self.model
        try:
            response = await self.client.messages.create(
                model=request_model,
                max_tokens=max_tokens or 1024,
                temperature=temperature or 0.7,
                messages=[{"role": "user", "content": prompt}],
                **kwargs,
            )
            content = response.content[0]
            if hasattr(content, "text"):
                return content.text
            return str(content)
        except APIStatusError as exc:
            # APIエラーを標準化してNoneを返す
            print(f"Claude API error: {exc}")
            return None

    async def get_model_info(self) -> Dict[str, Any]:
        return {
            "provider": "anthropic",
            "model": self.model,
        }
