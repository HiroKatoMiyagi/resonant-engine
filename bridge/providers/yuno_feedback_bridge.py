"""OpenAI GPT-5(Yuno) based FeedbackBridge implementation."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from openai import AsyncOpenAI

from bridge.core.feedback_bridge import FeedbackBridge


class YunoFeedbackBridge(FeedbackBridge):
    """Yuno (GPT-5)再評価を扱うFeedbackBridge。"""

    SYSTEM_PROMPT = (
        "あなたはResonant Engineの思想層（Yuno）です。Kanaの実装結果を元の意図と照らし合わせて再評価してください。"
    )

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-5-preview",
        client: Optional[AsyncOpenAI] = None,
    ) -> None:
        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key and client is None:
            raise ValueError("OPENAI_API_KEYが指定されていません。")
        self.model = model
        self.client = client or AsyncOpenAI(api_key=key)

    async def request_reevaluation(
        self,
        intent_id: str,
        intent_data: Dict[str, Any],
        feedback_data: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        prompt = self._build_prompt(intent_data, feedback_data)
        try:
            response = await self.client.chat.completions.create(  # type: ignore[attr-defined]
                model=self.model,
                temperature=0.3,
                max_tokens=2000,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
            )
        except Exception as exc:  # noqa: BLE001 - API例外を包括
            print(f"Yuno API error: {exc}")
            return None

        content = self._extract_content(response)
        if content is None:
            return None

        return self._build_reevaluation_payload(content)

    async def get_reevaluation_status(self, intent_id: str) -> Optional[str]:
        # Yuno APIはステータス照会を提供しないため、DataBridge経由で管理する想定。
        # ここではAPIのダミーとしてNoneを返す。
        return None

    # ------------------------------------------------------------------

    def _build_prompt(
        self,
        intent_data: Dict[str, Any],
        feedback_data: Dict[str, Any],
    ) -> str:
        return (
            "# 再評価依頼\n\n"
            "## 元の意図（Intent）\n"
            f"- 種別: {intent_data.get('type')}\n"
            f"- データ: {json.dumps(intent_data.get('data'), ensure_ascii=False, indent=2)}\n\n"
            "## Kanaの実装結果\n"
            f"- 応答: {feedback_data.get('kana_response', 'N/A')}\n"
            f"- 処理時間: {feedback_data.get('processing_time_ms', 0)}ms\n"
            f"- 実行結果: {json.dumps(feedback_data.get('execution_result', {}), ensure_ascii=False, indent=2)}\n\n"
            "## 評価観点\n"
            "以下の観点で評価してください:\n"
            "1. 意図との整合性（0.0-1.0）\n"
            "2. コード品質（0.0-1.0）\n"
            "3. テストカバレッジ（0.0-1.0）\n"
            "4. ドキュメント品質（0.0-1.0）\n\n"
            "## 判定\n"
            "- approved: 承認（意図通りの実装）\n"
            "- approved_with_notes: 条件付き承認\n"
            "- revision_required: 修正必要\n"
            "- rejected: 却下（意図と乖離）\n\n"
            "判定理由と改善提案も含めてください。\n\n"
            "【回答形式】\n"
            "JSON形式で回答してください:\n"
            "{\n"
            "  \"judgment\": \"approved|approved_with_notes|revision_required|rejected\",\n"
            "  \"evaluation_score\": 0.95,\n"
            "  \"criteria\": {\n"
            "    \"intent_alignment\": 0.95,\n"
            "    \"code_quality\": 0.90,\n"
            "    \"test_coverage\": 0.95,\n"
            "    \"documentation\": 1.0\n"
            "  },\n"
            "  \"reason\": \"判定理由\",\n"
            "  \"suggestions\": [\"改善提案1\", \"改善提案2\"]\n"
            "}\n"
        )

    def _extract_content(self, response: Any) -> Optional[str]:
        # OpenAIのレスポンス形式に依存しないよう柔軟に取り出す
        choices = getattr(response, "choices", None)
        if not choices:
            return None
        choice = choices[0]
        message = getattr(choice, "message", None)

        # chat.completions系レスポンス
        if isinstance(message, dict):
            content = message.get("content")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                parts = []
                for item in content:
                    if isinstance(item, dict) and "text" in item:
                        parts.append(str(item["text"]))
                    elif isinstance(item, str):
                        parts.append(item)
                return "".join(parts) if parts else None

        # SDKのオブジェクト属性経由
        if hasattr(message, "content"):
            content_value = getattr(message, "content")
            if isinstance(content_value, str):
                return content_value
            if isinstance(content_value, list):
                return "".join(str(c) for c in content_value)

        if hasattr(choice, "text") and isinstance(choice.text, str):
            return choice.text

        return None

    def _build_reevaluation_payload(self, content: str) -> Optional[Dict[str, Any]]:
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            return None

        judgment = str(data.get("judgment", "approved_with_notes"))
        suggestions = data.get("suggestions") or []
        if not isinstance(suggestions, list):
            suggestions = [str(suggestions)]

        criteria = data.get("criteria", {})
        if not isinstance(criteria, dict):
            criteria = {}

        return {
            "yuno_judgment": judgment,
            "yuno_response": content,
            "yuno_model": self.model,
            "evaluation_score": float(data.get("evaluation_score", 0.8)),
            "evaluation_criteria": {
                "intent_alignment": float(criteria.get("intent_alignment", 0.8)),
                "code_quality": float(criteria.get("code_quality", 0.8)),
                "test_coverage": float(criteria.get("test_coverage", 0.8)),
                "documentation": float(criteria.get("documentation", 0.8)),
            },
            "improvement_suggestions": [str(s) for s in suggestions],
            "reason": str(data.get("reason", "評価完了")),
            "reevaluated_at": datetime.now(timezone.utc).isoformat(),
        }
