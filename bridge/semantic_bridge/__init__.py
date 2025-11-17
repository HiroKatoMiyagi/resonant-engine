"""
Semantic Bridge System - L1: Event to Memory Unit Conversion Layer

This module provides functionality to convert events from the Intent pipeline
into semantic memory units that can be persisted and searched.
"""

from .models import (
    MemoryType,
    EmotionState,
    MemoryUnit,
    EventContext,
    InferenceResult,
    TypeInferenceRule,
    MemorySearchQuery,
)
from .extractor import SemanticExtractor
from .inferencer import TypeProjectInferencer
from .constructor import MemoryUnitConstructor
from .service import SemanticBridgeService
from .repositories import MemoryUnitRepository, InMemoryUnitRepository

__all__ = [
    # Models
    "MemoryType",
    "EmotionState",
    "MemoryUnit",
    "EventContext",
    "InferenceResult",
    "TypeInferenceRule",
    "MemorySearchQuery",
    # Components
    "SemanticExtractor",
    "TypeProjectInferencer",
    "MemoryUnitConstructor",
    "SemanticBridgeService",
    # Repositories
    "MemoryUnitRepository",
    "InMemoryUnitRepository",
]
