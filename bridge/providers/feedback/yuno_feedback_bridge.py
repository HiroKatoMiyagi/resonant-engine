"""Yuno (OpenAI) powered feedback bridge implementation."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI

from bridge.core.feedback_bridge import FeedbackBridge


class YunoFeedbackBridge(FeedbackBridge):
    """Call Yuno (GPT-5 preview) to perform re-evaluation and corrections."""

    SYSTEM_PROMPT = (
        "You are Yuno, the thought core of Resonant Engine. Re-evaluate intents and craft corrections."
    )

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-5-preview",
        client: Optional[AsyncOpenAI] = None,
    ) -> None:
        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key and client is None:
            raise ValueError("OPENAI_API_KEY must be configured for YunoFeedbackBridge")
        self._model = model
        self._client = client or AsyncOpenAI(api_key=key)

    async def request_reevaluation(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        prompt = self._build_prompt(intent, feedback_history=[])
        evaluation = await self._invoke(prompt)
        evaluation.setdefault("reevaluated_at", datetime.now(timezone.utc).isoformat())
        return evaluation

    async def submit_feedback(self, intent_id: str, feedback: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "intent_id": intent_id,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "feedback": feedback,
        }

    async def reanalyze(self, intent: Dict[str, Any], history: List[Dict[str, Any]]) -> Dict[str, Any]:
        prompt = self._build_prompt(intent, history)
        evaluation = await self._invoke(prompt)
        evaluation.setdefault("reevaluated_at", datetime.now(timezone.utc).isoformat())
        evaluation["history_count"] = len(history)
        return evaluation

    async def generate_correction(
        self,
        intent: Dict[str, Any],
        feedback_history: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        evaluation = await self.reanalyze(intent, feedback_history)
        return self._build_correction(intent, evaluation)

    async def _invoke(self, prompt: str) -> Dict[str, Any]:
        try:
            response = await self._client.chat.completions.create(  # type: ignore[attr-defined]
                model=self._model,
                temperature=0.3,
                max_tokens=2000,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
            )
        except Exception as exc:  # noqa: BLE001 - captured for resilience
            return {
                "status": "error",
                "reason": str(exc),
            }

        content = self._extract_content(response)
        if content is None:
            return {
                "status": "error",
                "reason": "empty-response",
            }
        return self._parse_evaluation(content)

    @staticmethod
    def _extract_content(response: Any) -> Optional[str]:
        choices = getattr(response, "choices", None)
        if not choices:
            return None
        message = getattr(choices[0], "message", None)
        if isinstance(message, dict):
            content = message.get("content")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                return "".join(str(item) for item in content)
        if hasattr(message, "content"):
            content_value = getattr(message, "content")
            if isinstance(content_value, str):
                return content_value
            if isinstance(content_value, list):
                return "".join(str(item) for item in content_value)
        if hasattr(choices[0], "text") and isinstance(choices[0].text, str):
            return choices[0].text
        return None

    def _build_prompt(self, intent: Dict[str, Any], feedback_history: List[Dict[str, Any]]) -> str:
        payload = intent.get("payload", {})
        sections = [
            "# Re-evaluation Request",
            "## Intent",
            f"- id: {intent.get('id', 'N/A')}",
            f"- type: {intent.get('type', 'unknown')}",
            f"- source: {intent.get('source', 'daemon')}",
            "- payload:",
            json.dumps(payload, ensure_ascii=False, indent=2),
            "",
        ]
        if feedback_history:
            sections.append("## Feedback History")
            for idx, feedback in enumerate(feedback_history, start=1):
                sections.append(f"### Entry {idx}")
                sections.append(json.dumps(feedback, ensure_ascii=False, indent=2))
                sections.append("")
        else:
            sections.append("## Feedback History\n- none")

        sections.append(
            "## Instructions\n"
            "Return JSON with: judgment, evaluation_score (0-1), criteria (intent_alignment, code_quality,"
            " test_coverage, documentation), reason, suggestions[], and optionally issues[], root_causes[],"
            " alternatives[]."
        )
        return "\n".join(sections)

    def _parse_evaluation(self, content: str) -> Dict[str, Any]:
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            return {
                "status": "error",
                "reason": "invalid-json",
                "raw": content,
            }
        criteria = data.get("criteria") or {}
        suggestions = data.get("suggestions") or []
        issues = data.get("issues") or []
        root_causes = data.get("root_causes") or []
        alternatives = data.get("alternatives") or []
        return {
            "status": "ok",
            "judgment": data.get("judgment", "approved_with_notes"),
            "evaluation_score": float(data.get("evaluation_score", 0.75)),
            "criteria": criteria,
            "reason": data.get("reason", ""),
            "suggestions": suggestions,
            "issues": issues,
            "root_causes": root_causes,
            "alternatives": alternatives,
            "raw": data,
        }

    @staticmethod
    def _build_correction(intent: Dict[str, Any], evaluation: Dict[str, Any]) -> Dict[str, Any]:
        suggestions = evaluation.get("suggestions") or []
        recommended_changes = [
            {
                "description": suggestion,
                "priority": "medium",
            }
            for suggestion in suggestions
        ] or [
            {
                "description": "Monitor intent outcome",
                "priority": "low",
            }
        ]
        return {
            "intent_id": intent.get("id"),
            "issues": evaluation.get("issues", []),
            "root_causes": evaluation.get("root_causes", []),
            "alternatives": evaluation.get("alternatives", []),
            "recommended_changes": recommended_changes,
            "confidence": evaluation.get("evaluation_score", 0.5),
            "evaluation": evaluation,
        }
