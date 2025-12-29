"""Shared lock session primitives."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.intent import IntentModel


@dataclass(slots=True)
class LockedIntentSession:
    """In-memory intent holder used while pessimistic locks are active."""

    intent: "IntentModel"

    def replace(self, updated: "IntentModel") -> "IntentModel":
        self.intent = updated
        return self.intent
