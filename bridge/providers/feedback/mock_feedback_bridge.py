"""Mock feedback bridge providing deterministic outputs."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from bridge.core.constants import PhilosophicalActor
from bridge.core.feedback_bridge import FeedbackBridge
from bridge.core.models.intent_model import IntentModel
from bridge.core.models.reeval import ReEvaluationRequest

if TYPE_CHECKING:  # pragma: no cover - import cycle guard
    from bridge.core.reeval_client import ReEvalClient


class MockFeedbackBridge(FeedbackBridge):
    """Return canned re-evaluation results for testing."""

    def __init__(
        self,
        judgment: str = "approved",
        *,
        correction_diff: Optional[Dict[str, Any]] = None,
        reeval_client: Optional["ReEvalClient"] = None,
        correction_reason: str = "Mock feedback correction",
    ) -> None:
        super().__init__(reeval_client)
        self._judgment = judgment
        self._correction_diff = correction_diff or {}
        self._correction_reason = correction_reason

    async def request_reevaluation(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "judgment": self._judgment,
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
            "notes": f"Mock reevaluation for {intent.get('type', 'unknown')}",
        }

    async def submit_feedback(self, intent_id: str, feedback: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "intent_id": intent_id,
            "status": "feedback-recorded",
            "stored_feedback": feedback,
        }

    async def reanalyze(self, intent: Dict[str, Any], history: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "intent": intent,
            "history_count": len(history),
            "judgment": self._judgment,
        }

    async def generate_correction(
        self,
        intent: Dict[str, Any],
        feedback_history: List[Dict[str, Any]],
        *,
        evaluation: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        diff_payload = dict(self._correction_diff) if self._correction_diff else {"status": "corrected"}
        return {
            "intent": intent,
            "issues": [],
            "recommended_changes": [
                {
                    "description": "No action required in mock mode",
                    "priority": "low",
                }
            ],
            "confidence": 0.9,
            "feedback_history_length": len(feedback_history),
            "applied_via_reeval": self.reeval_client is not None and bool(diff_payload),
            "diff": {"payload": diff_payload},
        }

    async def execute(
        self,
        intent: IntentModel,
        *,
        evaluation: Optional[Dict[str, Any]] = None,
        correction_plan: Optional[Dict[str, Any]] = None,
    ) -> IntentModel:
        """Trigger re-evaluation when the mock judgment requires changes."""

        if self.reeval_client is None:
            return intent

        if self._judgment.lower().startswith("approved") and not self._correction_diff:
            return intent

        diff_payload = dict(self._correction_diff)
        if not diff_payload:
            diff_payload = {"status": "corrected"}

        request = ReEvaluationRequest(
            intent_id=intent.id,
            diff={"payload": diff_payload},
            source=PhilosophicalActor.KANA,
            reason=self._correction_reason,
        )

        await self.reeval_client.reeval(request)
        return await self.reeval_client.get_intent(intent.intent_id)
