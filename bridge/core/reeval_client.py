"""Client wrapper around the Bridge Lite re-evaluation API."""

from __future__ import annotations

from typing import Union
from uuid import UUID

from bridge.core.audit_logger import AuditLogger
from bridge.core.data_bridge import DataBridge
from bridge.core.models.intent_model import IntentModel
from bridge.core.models.reeval import ReEvaluationRequest, ReEvaluationResponse


class ReEvalClient:
    """Convenience wrapper to invoke the re-evaluation endpoint with shared dependencies."""

    def __init__(self, data_bridge: DataBridge, audit_logger: AuditLogger) -> None:
        self._data_bridge = data_bridge
        self._audit_logger = audit_logger

    async def reeval(self, request: ReEvaluationRequest) -> ReEvaluationResponse:
        """Apply a correction using the shared data bridge and audit logger."""
        from bridge.api.reeval import reeval_intent
        return await reeval_intent(request, data_bridge=self._data_bridge, audit_logger=self._audit_logger)

    async def get_intent(self, intent_id: Union[str, UUID]) -> IntentModel:
        """Retrieve the latest intent state from the data bridge."""

        return await self._data_bridge.get_intent(str(intent_id))


__all__ = ["ReEvalClient"]
