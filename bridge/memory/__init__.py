"""
Memory Management System for Resonant Engine

This module provides persistent storage for:
- Intent history and lifecycle
- Resonance state archives
- Agent context preservation
- Choice points management
- Breathing cycle tracking
- Temporal snapshots

Philosophy: Memory = Breath History + Resonance Traces
"""

from bridge.memory.models import (
    Session,
    SessionStatus,
    Intent,
    IntentStatus,
    IntentType,
    Resonance,
    ResonanceState,
    AgentContext,
    AgentType,
    ChoicePoint,
    Choice,
    BreathingCycle,
    BreathingPhase,
    Snapshot,
    SnapshotType,
)

__all__ = [
    "Session",
    "SessionStatus",
    "Intent",
    "IntentStatus",
    "IntentType",
    "Resonance",
    "ResonanceState",
    "AgentContext",
    "AgentType",
    "ChoicePoint",
    "Choice",
    "BreathingCycle",
    "BreathingPhase",
    "Snapshot",
    "SnapshotType",
]
