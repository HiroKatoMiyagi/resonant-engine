"""Backward-compatible enumeration aliases for Bridge Lite."""

from __future__ import annotations

from bridge.core.constants import (
    ActorEnum,
    AuditEventType,
    BridgeRoleEnum,
    BridgeTypeEnum,
    IntentStatusEnum,
    IntentTypeEnum,
    PhilosophicalActor,
    TechnicalActor,
)


# v2.0 names retained for gradual migration
IntentStatus = IntentStatusEnum
BridgeType = BridgeTypeEnum
IntentActor = TechnicalActor
PhilosophicalIntentActor = PhilosophicalActor
IntentType = IntentTypeEnum
LegacyBridgeType = BridgeRoleEnum
AuditEvent = AuditEventType

