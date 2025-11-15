"""FastAPI router providing the Bridge Lite re-evaluation endpoint."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status

from bridge.core.audit_logger import AuditLogger
from bridge.core.constants import (
    AuditEventType,
    BridgeTypeEnum,
    LogSeverity,
    PhilosophicalActor,
)
from bridge.core.correction.diff import validate_diff
from bridge.core.data_bridge import DataBridge
from bridge.core.exceptions import DiffApplicationError, DiffValidationError, InvalidStatusError
from bridge.core.models.intent_model import IntentModel
from bridge.core.models.reeval import ReEvaluationRequest, ReEvaluationResponse
from bridge.factory.bridge_factory import BridgeFactory

router = APIRouter(prefix="/api/v1/intent", tags=["re-evaluation"])


async def get_data_bridge() -> DataBridge:
    bridge = getattr(get_data_bridge, "_instance", None)
    if bridge is None:
        bridge = BridgeFactory.create_data_bridge()
        setattr(get_data_bridge, "_instance", bridge)
    if not getattr(bridge, "_connected", False):
        await bridge.connect()
    return bridge


async def get_audit_logger() -> AuditLogger:
    logger = getattr(get_audit_logger, "_instance", None)
    if logger is None:
        logger = BridgeFactory.create_audit_logger()
        setattr(get_audit_logger, "_instance", logger)
    if hasattr(logger, "connect") and not getattr(logger, "_connected", False):
        await getattr(logger, "connect")()  # type: ignore[misc]
    return logger


@router.post(
    "/reeval",
    response_model=ReEvaluationResponse,
    status_code=status.HTTP_200_OK,
    tags=["re-evaluation"],
    summary="Re-evaluate and correct an Intent",
    description="""
    Apply differential corrections to an Intent based on feedback from Yuno or Kana.

    This endpoint is typically called automatically by FeedbackBridge implementations
    (YunoFeedbackBridge, MockFeedbackBridge) when corrections are needed.

    **Idempotency**: Same (intent_id + diff) combination will return `already_applied: true`
    on subsequent calls without modifying the Intent.

    **Authorization**: Only YUNO and KANA sources are permitted. TSUMU is rejected.

    **Diff Format**:
    - Use absolute values only (no relative operators like "+5")
    - Nested fields use dot notation (e.g., "payload.feedback.yuno.reason")
    - See Sprint 1 specification for full diff rules
    """,
    responses={
        200: {
            "description": "Intent successfully re-evaluated",
            "content": {
                "application/json": {
                    "example": {
                        "intent_id": "550e8400-e29b-41d4-a716-446655440000",
                        "status": "corrected",
                        "already_applied": False,
                        "correction_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
                        "applied_at": "2025-11-15T12:34:56.789Z",
                        "correction_count": 1,
                    }
                }
            },
        },
        400: {"description": "Invalid diff format or validation error"},
        403: {"description": "Source not authorized for re-evaluation"},
        404: {"description": "Intent not found"},
        409: {"description": "Intent in non-correctable status"},
    },
)
async def reeval_intent(
    request: ReEvaluationRequest,
    data_bridge: DataBridge = Depends(get_data_bridge),
    audit_logger: AuditLogger = Depends(get_audit_logger),
) -> ReEvaluationResponse:
    """Apply a differential correction to an intent using FeedbackBridge-generated diffs."""

    intent_id_str = str(request.intent_id)

    try:
        intent = await data_bridge.get_intent(intent_id_str)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error_code": "INTENT_NOT_FOUND", "message": f"Intent {intent_id_str} not found"},
        ) from exc

    if request.source not in {PhilosophicalActor.YUNO, PhilosophicalActor.KANA}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error_code": "INVALID_SOURCE", "message": "Source actor not authorized for re-evaluation"},
        )

    try:
        validate_diff(request.diff)
        updated_intent, correction_record, already_applied = intent.apply_correction(
            request.diff,
            source=request.source,
            reason=request.reason,
            metadata=request.metadata,
        )
    except DiffValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "INVALID_DIFF", "message": str(exc)},
        ) from exc
    except DiffApplicationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "APPLY_FAILED", "message": str(exc)},
        ) from exc
    except InvalidStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error_code": "INVALID_STATUS", "message": str(exc)},
        ) from exc

    if already_applied:
        persisted_intent = intent
    else:
        persisted_intent = await data_bridge.update_intent(updated_intent)
        persisted_intent = await data_bridge.save_correction(
            persisted_intent.intent_id,
            correction_record.model_dump(mode="json", exclude_none=True),
        )

    log_details: Dict[str, Any] = {
        "correction_id": str(correction_record.correction_id),
        "already_applied": already_applied,
        "source": request.source.value,
        "reason": request.reason,
    }
    if request.metadata:
        log_details["metadata"] = request.metadata

    await audit_logger.log(
        bridge_type=BridgeTypeEnum.FEEDBACK,
        operation=AuditEventType.REEVALUATED.value,
        details=log_details,
        intent_id=persisted_intent.intent_id,
        correlation_id=str(persisted_intent.correlation_id),
        event=AuditEventType.REEVALUATED,
        severity=LogSeverity.INFO if not already_applied else LogSeverity.DEBUG,
    )

    return ReEvaluationResponse(
        intent_id=persisted_intent.id,
        status=persisted_intent.status,
        already_applied=already_applied,
        correction_id=correction_record.correction_id,
        applied_at=correction_record.applied_at,
        correction_count=len(persisted_intent.correction_history),
    )


__all__ = ["router", "reeval_intent", "get_data_bridge", "get_audit_logger"]
