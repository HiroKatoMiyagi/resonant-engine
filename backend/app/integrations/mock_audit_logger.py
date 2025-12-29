"""Mock audit logger storing entries in memory."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.integrations.audit_logger import AuditLogger
from app.services.shared.constants import AuditEventType, BridgeTypeEnum, LogSeverity


class MockAuditLogger(AuditLogger):
    """Collect audit logs for assertions in tests."""

    def __init__(self) -> None:
        self.entries: List[Dict[str, Any]] = []

    async def log(
        self,
        bridge_type: BridgeTypeEnum,
        operation: str,
        details: Dict[str, Any],
        intent_id: Optional[str],
        correlation_id: Optional[str] = None,
        event: Optional[AuditEventType] = None,
        severity: LogSeverity = LogSeverity.INFO,
    ) -> None:
        self.entries.append(
            {
                "bridge_type": bridge_type.value,
                "operation": operation,
                "details": details,
                "intent_id": intent_id,
                "correlation_id": correlation_id,
                "event": event.value if isinstance(event, AuditEventType) else None,
                "severity": severity.value,
            }
        )

    async def cleanup(self) -> None:
        self.entries.clear()
