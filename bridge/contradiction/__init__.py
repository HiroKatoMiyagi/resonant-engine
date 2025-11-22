"""Contradiction Detection Layer - Sprint 11

This module implements contradiction detection for Intent processing,
identifying conflicts with past decisions, policy shifts, duplicate work,
and unverified assumptions (dogma).

Philosophy:
    矛盾 = 呼吸の乱れ（認知的不協和の検出）
    Contradiction = Detecting cognitive dissonance / disrupted breathing
"""

from .models import Contradiction, IntentRelation
from .detector import ContradictionDetector

__all__ = ["Contradiction", "IntentRelation", "ContradictionDetector"]
