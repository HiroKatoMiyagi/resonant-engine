"""Aggregated container for Bridge Lite component instances."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, ClassVar, Dict, Optional, TYPE_CHECKING

from app.integrations.audit_logger import AuditLogger
from app.services.shared.constants import (
    AuditEventType,
    BridgeTypeEnum,
    ExecutionMode,
    IntentStatusEnum,
    LogSeverity,
)
from .ai_bridge import AIBridge
from .data_bridge import DataBridge
from .feedback_bridge import FeedbackBridge

if TYPE_CHECKING:
    from app.models.intent import IntentModel, CorrectionRecord


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class BridgeSet:
    """Convenient wrapper bundling the active bridge implementations."""

    data: DataBridge
    ai: AIBridge
    feedback: FeedbackBridge
    audit: AuditLogger

    PIPELINE_ORDER: ClassVar[tuple[BridgeTypeEnum, ...]] = (
        BridgeTypeEnum.INPUT,
        BridgeTypeEnum.NORMALIZE,
        BridgeTypeEnum.FEEDBACK,
        BridgeTypeEnum.OUTPUT,
    )

    async def connect(self) -> "BridgeSet":
        """Initialise underlying bridges where applicable."""

        if hasattr(self.data, "connect"):
            await self.data.connect()
        if hasattr(self.audit, "connect"):
            await getattr(self.audit, "connect")()  # type: ignore[misc]
        return self

    async def disconnect(self) -> None:
        """Release bridge resources gracefully."""

        if hasattr(self.audit, "close"):
            await getattr(self.audit, "close")()  # type: ignore[misc]
        if hasattr(self.audit, "disconnect"):
            await getattr(self.audit, "disconnect")()  # type: ignore[misc]
        if hasattr(self.data, "disconnect"):
            await self.data.disconnect()

    async def __aenter__(self) -> "BridgeSet":
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        await self.disconnect()

    def as_tuple(self) -> tuple[DataBridge, AIBridge, FeedbackBridge, AuditLogger]:
        """Return bridges as a tuple preserving creation order."""

        return (self.data, self.ai, self.feedback, self.audit)

    async def execute(
        self,
        intent: "IntentModel",
        *,
        mode: ExecutionMode = ExecutionMode.FAILFAST,
    ) -> "IntentModel":
        """Execute the standard pipeline against an intent."""

        if hasattr(self.data, "lock_intent_for_update"):
            try:
                return await self.execute_with_lock(
                    intent.intent_id,
                    mode=mode,
                    initial_intent=intent,
                )
            except KeyError:
                # Intent is not yet persisted; fall back to optimistic execution
                pass
        return await self._execute_pipeline(intent, mode=mode)

    async def execute_with_lock(
        self,
        intent_id: str,
        *,
        initial_intent: Optional["IntentModel"] = None,
        mode: ExecutionMode = ExecutionMode.FAILFAST,
    ) -> "IntentModel":
        """Convenience wrapper that locks the intent before executing the pipeline."""
        # Import retry decorator here to avoid circular dependency
        from app.services.intent.concurrency import retry_on_deadlock
        
        @retry_on_deadlock()
        async def _execute_locked():
            async with self.data.lock_intent_for_update(intent_id) as locked:
                if initial_intent is not None:
                    locked.replace(initial_intent)
                result = await self._execute_pipeline(locked.intent, mode=mode)
                return locked.replace(result)
        
        return await _execute_locked()

    async def _execute_pipeline(
        self,
        intent: "IntentModel",
        *,
        mode: ExecutionMode = ExecutionMode.FAILFAST,
    ) -> "IntentModel":
        current = intent
        for stage in self.PIPELINE_ORDER:
            try:
                await self._log_event(stage, AuditEventType.BRIDGE_STARTED, current)
                current = await self._run_stage(stage, current)
                await self._log_event(stage, AuditEventType.BRIDGE_COMPLETED, current)
            except Exception as exc:  # pragma: no cover - defensive path
                await self._log_event(
                    stage,
                    AuditEventType.BRIDGE_FAILED,
                    current,
                    severity=LogSeverity.ERROR,
                    extra={"error": str(exc)},
                )
                current = current.with_updates(status=IntentStatusEnum.FAILED, updated_at=_utcnow())
                if mode == ExecutionMode.FAILFAST or stage == BridgeTypeEnum.INPUT and mode == ExecutionMode.SELECTIVE:
                    raise
                continue
        return current

    async def _run_stage(self, stage: BridgeTypeEnum, intent: "IntentModel") -> "IntentModel":
        # Import CorrectionRecord here to avoid circular dependency
        from app.models.intent import CorrectionRecord
        
        if stage == BridgeTypeEnum.INPUT:
            persisted = await self.data.save_intent(intent)
            normalized = persisted.with_updates(status=IntentStatusEnum.NORMALIZED, updated_at=_utcnow())
            if hasattr(self.data, "update_intent_status"):
                try:
                    normalized = await getattr(self.data, "update_intent_status")(
                        normalized.intent_id,
                        IntentStatusEnum.NORMALIZED.value,
                    )
                except TypeError:
                    normalized = await getattr(self.data, "update_intent_status")(
                        normalized.intent_id,
                        IntentStatusEnum.NORMALIZED,
                    )
            return normalized

        if stage == BridgeTypeEnum.NORMALIZE:
            ai_result = await self.ai.process_intent(intent.model_dump_bridge())
            payload = copy.deepcopy(intent.payload)
            payload.setdefault("analysis", ai_result)
            return intent.with_updates(
                payload=payload,
                status=IntentStatusEnum.PROCESSED,
                updated_at=_utcnow(),
            )

        if stage == BridgeTypeEnum.FEEDBACK:
            feedback_result = await self.feedback.reanalyze(
                intent.model_dump_bridge(),
                intent.correction_history,
            )
            feedback_record = CorrectionRecord.model_validate(
                {
                    "reason": "feedback-analysis",
                    "metadata": {
                        "stage": "feedback",
                        "result": feedback_result,
                    },
                }
            )
            corrections = list(intent.correction_history)
            corrections.append(feedback_record)
            status = intent.status
            updated_intent = intent.with_updates(
                correction_history=corrections,
                updated_at=_utcnow(),
            )
            if hasattr(self.feedback, "generate_correction"):
                correction_plan = await self.feedback.generate_correction(
                    updated_intent.model_dump_bridge(),
                    [feedback_result],
                    evaluation=feedback_result,
                )
                correction_record = CorrectionRecord.model_validate(
                    {
                        "reason": "feedback-correction",
                        "diff": correction_plan.get("diff") or {},
                        "metadata": {
                            "stage": "correction",
                            "plan": correction_plan,
                        },
                    }
                )
                corrections.append(correction_record)
                updated_intent = updated_intent.with_updates(
                    correction_history=corrections,
                    updated_at=_utcnow(),
                )
                updated_intent = await self.feedback.execute(
                    updated_intent,
                    evaluation=feedback_result,
                    correction_plan=correction_plan,
                )
                latest_record = updated_intent.correction_history[-1] if updated_intent.correction_history else None
                persist_payload = {
                    "status": IntentStatusEnum.CORRECTED.value,
                    "correction_plan": correction_plan,
                    "feedback": feedback_result,
                    "generated_at": correction_record.applied_at.isoformat(),
                    "diff": correction_plan.get("diff"),
                }
                if latest_record is not None:
                    persist_payload.setdefault("correction_id", latest_record.correction_id)
                    persist_payload.setdefault("applied_at", latest_record.applied_at)
                    persist_payload.setdefault("source", latest_record.source.value)
                updated_intent = await self.data.save_correction(updated_intent.intent_id, persist_payload)
                status = IntentStatusEnum.CORRECTED
                updated_intent = updated_intent.with_updates(updated_at=_utcnow())
            return updated_intent.with_updates(status=status)

        if stage == BridgeTypeEnum.OUTPUT:
            target_status = (
                IntentStatusEnum.COMPLETED
                if intent.status not in {IntentStatusEnum.FAILED}
                else intent.status
            )
            if hasattr(self.data, "update_intent_status"):
                try:
                    intent = await getattr(self.data, "update_intent_status")(
                        intent.intent_id,
                        target_status.value,
                    )
                except TypeError:
                    intent = await getattr(self.data, "update_intent_status")(
                        intent.intent_id,
                        target_status,
                    )
            return intent.with_updates(status=target_status, updated_at=_utcnow())

        return intent

    async def _log_event(
        self,
        stage: BridgeTypeEnum,
        event: AuditEventType,
        intent: "IntentModel",
        *,
        severity: LogSeverity = LogSeverity.INFO,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        details: Dict[str, Any] = {"stage": stage.value}
        if extra:
            details.update(extra)
        await self.audit.log(
            bridge_type=stage,
            operation=event.value,
            details=details,
            intent_id=intent.intent_id,
            correlation_id=str(intent.correlation_id),
            event=event,
            severity=severity,
        )
