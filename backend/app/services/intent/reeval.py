"""Client wrapper around the Bridge Lite re-evaluation functionality."""

from __future__ import annotations

from typing import Union, TYPE_CHECKING
from uuid import UUID

from app.integrations.audit_logger import AuditLogger
from app.services.shared.constants import AuditEventType, LogSeverity
from .data_bridge import DataBridge

if TYPE_CHECKING:
    from app.models.intent import IntentModel
    from app.models.reeval import ReEvaluationRequest, ReEvaluationResponse


class ReEvalClient:
    """Convenience wrapper to invoke re-evaluation with shared dependencies."""

    def __init__(self, data_bridge: DataBridge, audit_logger: AuditLogger) -> None:
        self._data_bridge = data_bridge
        self._audit_logger = audit_logger

    async def reeval(self, request: "ReEvaluationRequest") -> "ReEvaluationResponse":
        """Apply a correction to an intent.
        
        This method:
        1. Retrieves the intent from data bridge
        2. Applies the correction using IntentModel.apply_correction
        3. Saves the updated intent
        4. Logs the audit event
        5. Returns the response
        """
        # Import here to avoid circular dependency
        from app.models.reeval import ReEvaluationResponse
        
        # Get current intent
        intent = await self._data_bridge.get_intent(str(request.intent_id))
        
        # Apply correction
        updated_intent, correction_record, already_applied = intent.apply_correction(
            diff=request.diff,
            source=request.source,
            reason=request.reason,
            metadata=request.metadata,
        )
        
        if not already_applied:
            # Save updated intent
            await self._data_bridge.save_intent(updated_intent)
            
            # Log audit event
            await self._audit_logger.log(
                event_type=AuditEventType.CORRECTION_APPLIED,
                intent_id=str(request.intent_id),
                severity=LogSeverity.INFO,
                details={
                    "correction_id": str(correction_record.correction_id),
                    "source": request.source.value if hasattr(request.source, 'value') else str(request.source),
                    "reason": request.reason,
                    "diff": request.diff,
                },
            )
        
        return ReEvaluationResponse(
            intent_id=request.intent_id,
            status=updated_intent.status.value,
            already_applied=already_applied,
            correction_id=correction_record.correction_id,
            applied_at=correction_record.applied_at,
            correction_count=len(updated_intent.correction_history),
        )

    async def get_intent(self, intent_id: Union[str, UUID]) -> "IntentModel":
        """Retrieve the latest intent state from the data bridge."""
        return await self._data_bridge.get_intent(str(intent_id))


async def reeval_intent(
    request: "ReEvaluationRequest",
    data_bridge: DataBridge,
    audit_logger: AuditLogger
) -> "ReEvaluationResponse":
    """Standalone function for backward compatibility."""
    client = ReEvalClient(data_bridge, audit_logger)
    return await client.reeval(request)


__all__ = ["ReEvalClient", "reeval_intent"]
