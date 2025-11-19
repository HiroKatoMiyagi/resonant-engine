"""
User Profile Management Module

Sprint 8: User Profile & Persistent Context
CLAUDE.mdのユーザー情報をデータベース化し、Context Assemblerに統合
"""

from .models import (
    UserProfile,
    CognitiveTrait,
    FamilyMember,
    UserGoal,
    ResonantConcept,
    UserProfileData,
)
from .repository import UserProfileRepository
from .context_provider import ProfileContextProvider, ProfileContext

__all__ = [
    "UserProfile",
    "CognitiveTrait",
    "FamilyMember",
    "UserGoal",
    "ResonantConcept",
    "UserProfileData",
    "UserProfileRepository",
    "ProfileContextProvider",
    "ProfileContext",
]
