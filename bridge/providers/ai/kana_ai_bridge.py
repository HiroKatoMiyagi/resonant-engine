"""Kana (Anthropic Claude) AI bridge implementation."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

from anthropic import APIStatusError, AsyncAnthropic

from bridge.core.ai_bridge import AIBridge


class KanaAIBridge(AIBridge):
    """Wrap Anthropic Claude as the Kana intent processor with conversation memory."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-haiku-20240307",
        client: Optional[AsyncAnthropic] = None,
        context_assembler: Optional[Any] = None,  # ContextAssemblerService
    ) -> None:
        key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not key and client is None:
            raise ValueError("ANTHROPIC_API_KEY must be configured for KanaAIBridge")
        self._model = model
        self._client = client or AsyncAnthropic(api_key=key)
        self._context_assembler = context_assembler

    async def process_intent(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process intent with context memory support.

        Args:
            intent: Intent dict with fields:
                - content: str (user message) - required
                - user_id: str - optional, default "default"
                - session_id: UUID - optional

        Returns:
            Response dict with status, summary, and optional context_metadata
        """
        user_message = intent.get("content")
        user_id = intent.get("user_id", "default")
        session_id = intent.get("session_id")

        # Context Assemblerが設定されている場合、文脈を構築
        if self._context_assembler and user_message:
            try:
                assembled = await self._context_assembler.assemble_context(
                    user_message=user_message,
                    user_id=user_id,
                    session_id=session_id,
                )
                messages = assembled.messages
                context_metadata = assembled.metadata
            except Exception as e:
                # Context組み立てに失敗した場合はfallback
                import warnings

                warnings.warn(
                    f"Context assembly failed: {e}, falling back to simple mode"
                )
                messages = self._build_simple_messages(intent)
                context_metadata = None
        else:
            # Context Assembler未設定または古い形式のintent
            messages = self._build_simple_messages(intent)
            context_metadata = None

        # Claude API呼び出し
        # systemメッセージを分離
        system_content = None
        user_messages = []
        
        for msg in messages:
            if msg.get("role") == "system":
                system_content = msg.get("content")
            else:
                user_messages.append(msg)
        
        try:
            # Messages API v2: systemは別パラメータ
            api_params = {
                "model": self._model,
                "max_tokens": 4096,
                "temperature": 0.5,
                "messages": user_messages,
            }
            
            if system_content:
                api_params["system"] = system_content
            
            response = await self._client.messages.create(**api_params)  # type: ignore[attr-defined]
        except APIStatusError as exc:  # pragma: no cover - network failure path
            return {
                "status": "error",
                "reason": str(exc),
            }

        message = response.content[0]
        summary = getattr(message, "text", None) or str(message)

        result = {
            "status": "ok",
            "model": self._model,
            "summary": summary,
        }

        # Context metadata追加
        if context_metadata:
            result["context_metadata"] = {
                "working_memory_count": context_metadata.working_memory_count,
                "semantic_memory_count": context_metadata.semantic_memory_count,
                "has_session_summary": context_metadata.has_session_summary,
                "total_tokens": context_metadata.total_tokens,
                "compression_applied": context_metadata.compression_applied,
            }

        return result

    def _build_simple_messages(self, intent: Dict[str, Any]) -> list:
        """Fallback: シンプルなメッセージリスト（従来の動作）"""
        # contentフィールドがあればそれを使用、なければ古い形式
        user_message = intent.get("content") or self._build_prompt(intent)

        return [
            {
                "role": "system",
                "content": "You are Kana, the external translator for Resonant Engine.",
            },
            {
                "role": "user",
                "content": user_message,
            },
        ]

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
