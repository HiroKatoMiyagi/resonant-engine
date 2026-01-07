"""Yuno (OpenAI) powered feedback bridge implementation."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI

from app.services.shared.constants import PhilosophicalActor
from app.services.intent.feedback_bridge import FeedbackBridge
from app.services.intent.reeval import ReEvalClient


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
        *,
        reeval_client: Optional[ReEvalClient] = None,
    ) -> None:
        super().__init__(reeval_client)
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
        *,
        evaluation: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        evaluation_result = evaluation or await self.reanalyze(intent, feedback_history)
        return self._build_correction(intent, evaluation_result, feedback_history)

    async def execute(
        self,
        intent: Any,  # IntentModel
        *,
        evaluation: Optional[Dict[str, Any]] = None,
        correction_plan: Optional[Dict[str, Any]] = None,
    ) -> Any:
        if self.reeval_client is None:
            return intent

        evaluation_result = evaluation
        plan = correction_plan

        if plan is None or evaluation_result is None:
            payload_view = intent.model_dump_bridge()
            evaluation_result = evaluation_result or await self.reanalyze(
                payload_view,
                intent.correction_history,
            )
            if evaluation_result.get("status") == "error":
                return intent
            plan = await self.generate_correction(
                payload_view,
                intent.correction_history,
                evaluation=evaluation_result,
            )

        if not plan or evaluation_result is None or evaluation_result.get("status") == "error":
            return intent

        diff = plan.get("diff")
        if not isinstance(diff, dict) or not diff.get("payload"):
            return intent

        metadata = {
            "provider": "yuno",
            "evaluation": evaluation_result,
            "recommended_changes": plan.get("recommended_changes"),
            "generated_at": plan.get("generated_at"),
        }

        # Import here to avoid circular dependency
        from app.models.reeval import ReEvaluationRequest
        
        request = ReEvaluationRequest(
            intent_id=intent.id,
            diff=diff,
            source=PhilosophicalActor.YUNO,
            reason=plan.get("reason", "Yuno feedback correction"),
            metadata=metadata,
        )

        await self.reeval_client.reeval(request)
        return await self.reeval_client.get_intent(intent.intent_id)

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
        status = data.get("status", "ok")
        criteria = data.get("criteria") or {}
        suggestions = data.get("suggestions") or []
        issues = data.get("issues") or []
        root_causes = data.get("root_causes") or []
        alternatives = data.get("alternatives") or []
        return {
            "status": status,
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

    def _build_correction(
        self,
        intent: Dict[str, Any],
        evaluation: Dict[str, Any],
        feedback_history: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        suggestions = evaluation.get("suggestions") or []
        recommended_changes = [
            {
                "description": suggestion if isinstance(suggestion, str) else json.dumps(suggestion, ensure_ascii=False),
                "priority": "medium",
            }
            for suggestion in suggestions
        ] or [
            {
                "description": "Monitor intent outcome",
                "priority": "low",
            }
        ]

        confidence = float(evaluation.get("evaluation_score", 0.5))
        reason = evaluation.get("reason") or "Yuno feedback correction"
        generated_at = datetime.now(timezone.utc).isoformat()

        feedback_entry = {
            "status": evaluation.get("status", "ok"),
            "judgment": evaluation.get("judgment"),
            "reason": evaluation.get("reason"),
            "evaluation_score": confidence,
            "criteria": evaluation.get("criteria"),
            "issues": evaluation.get("issues", []),
            "root_causes": evaluation.get("root_causes", []),
            "alternatives": evaluation.get("alternatives", []),
            "history_count": len(feedback_history),
            "generated_at": generated_at,
        }

        diff = {
            "payload": {
                "feedback.yuno.latest": feedback_entry,
                "feedback.yuno.recommended_changes": recommended_changes,
                "feedback.yuno.reason": reason,
                "feedback.yuno.confidence": confidence,
            }
        }

        return {
            "intent_id": intent.get("id"),
            "issues": feedback_entry["issues"],
            "root_causes": feedback_entry["root_causes"],
            "alternatives": feedback_entry["alternatives"],
            "recommended_changes": recommended_changes,
            "confidence": confidence,
            "evaluation": evaluation,
            "reason": reason,
            "diff": diff,
            "applied_via_reeval": self.reeval_client is not None,
            "generated_at": generated_at,
        }


# Alias
OpenAIClient = YunoFeedbackBridge


class YunoAIBridge:
    """OpenAI/ChatGPT-based AI Bridge for conversation (similar to KanaAIBridge)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o",
        client: Optional[AsyncOpenAI] = None,
    ) -> None:
        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key and client is None:
            raise ValueError("OPENAI_API_KEY must be configured for YunoAIBridge")
        self._model = model
        self._client = client or AsyncOpenAI(api_key=key)

    async def process_intent(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process intent and generate AI response using OpenAI.

        Args:
            intent: Intent dict with fields:
                - content: str (user message) - required
                - user_id: str - optional

        Returns:
            Response dict with status and summary
        """
        user_message = intent.get("content", "")
        
        messages = [
            {
                "role": "system",
                "content": """You are Yuno, an intelligent assistant for the Resonant Engine system.
You help users with their questions and tasks in a friendly and helpful manner.
Respond in Japanese unless the user writes in English.
Be concise but thorough in your responses.""",
            },
            {
                "role": "user",
                "content": user_message,
            },
        ]

        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                max_tokens=4096,
                temperature=0.5,
                messages=messages,
            )
        except Exception as exc:
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

        return {
            "status": "ok",
            "model": self._model,
            "summary": content,
        }

    @staticmethod
    def _extract_content(response: Any) -> Optional[str]:
        choices = getattr(response, "choices", None)
        if not choices:
            return None
        message = getattr(choices[0], "message", None)
        if message and hasattr(message, "content"):
            return message.content
        return None

