"""Alert configuration primitives for Sprint 3."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, List, Sequence


class AlertSeverity(str, Enum):
    """Severity levels supported by the alerting system."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertChannel(str, Enum):
    """Channels that can receive alert notifications."""

    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    LOG = "log"


@dataclass(slots=True)
class AlertRule:
    """Declarative alert rule that maps directly to the Sprint 3 spec."""

    name: str
    description: str
    severity: AlertSeverity
    condition: str
    threshold: float
    cooldown_minutes: int = 5
    channels: Sequence[AlertChannel] | None = None

    def __post_init__(self) -> None:  # pragma: no cover - metadata normalization
        if self.channels is None:
            self.channels = []
        elif not isinstance(self.channels, list):
            self.channels = list(self.channels)


DEFAULT_ALERT_RULES: List[AlertRule] = [
    AlertRule(
        name="high_error_rate",
        description="Error rate exceeds 5% in last 10 minutes",
        severity=AlertSeverity.ERROR,
        condition=
        """
        SELECT 
            COALESCE(
                COUNT(CASE WHEN status = 'failed' THEN 1 END)::float / NULLIF(COUNT(*), 0),
                0
            )
        FROM intents
        WHERE created_at > NOW() - INTERVAL '10 minutes'
        """,
        threshold=0.05,
        cooldown_minutes=10,
        channels=[AlertChannel.SLACK, AlertChannel.EMAIL],
    ),
    AlertRule(
        name="high_correction_rate",
        description="Correction rate exceeds 20% in last hour",
        severity=AlertSeverity.WARNING,
        condition=
        """
        SELECT 
            COALESCE(
                COUNT(CASE WHEN jsonb_array_length(correction_history) > 0 THEN 1 END)::float / NULLIF(COUNT(*), 0),
                0
            )
        FROM intents
        WHERE created_at > NOW() - INTERVAL '1 hour'
        """,
        threshold=0.20,
        cooldown_minutes=30,
        channels=[AlertChannel.SLACK],
    ),
    AlertRule(
        name="slow_processing",
        description="Average processing time exceeds 5 seconds",
        severity=AlertSeverity.WARNING,
        condition=
        """
        SELECT AVG(duration_ms) / 1000.0 AS avg_seconds
        FROM audit_logs_ts
        WHERE time > NOW() - INTERVAL '10 minutes'
          AND event_type = 'BRIDGE_COMPLETED'
        """,
        threshold=5.0,
        cooldown_minutes=15,
        channels=[AlertChannel.LOG],
    ),
    AlertRule(
        name="no_activity",
        description="No intents created in last 30 minutes",
        severity=AlertSeverity.INFO,
        condition=
        """
        SELECT COUNT(*)::float
        FROM intents
        WHERE created_at > NOW() - INTERVAL '30 minutes'
        """,
        threshold=1.0,
        cooldown_minutes=30,
        channels=[AlertChannel.LOG],
    ),
]

__all__ = [
    "AlertSeverity",
    "AlertChannel",
    "AlertRule",
    "DEFAULT_ALERT_RULES",
]
