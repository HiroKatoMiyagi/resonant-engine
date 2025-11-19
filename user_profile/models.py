"""
User Profile Data Models

Sprint 8: User Profile & Persistent Context
Pydanticモデル定義
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from uuid import UUID


class UserProfile(BaseModel):
    """ユーザープロフィール基本情報"""

    id: Optional[UUID] = None
    user_id: str
    full_name: Optional[str] = None
    birth_date: Optional[date] = None
    location: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_sync_at: Optional[datetime] = None
    encryption_key_id: Optional[str] = None
    is_active: bool = True

    class Config:
        from_attributes = True  # Pydantic v2


class CognitiveTrait(BaseModel):
    """認知特性（ASD等）"""

    id: Optional[UUID] = None
    user_id: str
    trait_type: str = Field(..., description="asd_trigger, asd_preference, asd_strength")
    trait_name: str
    description: Optional[str] = None
    importance_level: str = Field(default="medium", description="critical, high, medium, low")
    handling_strategy: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FamilyMember(BaseModel):
    """家族メンバー"""

    id: Optional[UUID] = None
    user_id: str
    name: str
    relationship: str = Field(..., description="spouse, child, parent")
    birth_date: Optional[date] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    encryption_key_id: Optional[str] = None

    class Config:
        from_attributes = True


class UserGoal(BaseModel):
    """ユーザー目標"""

    id: Optional[UUID] = None
    user_id: str
    goal_category: str = Field(..., description="financial, project, research, family")
    goal_title: str
    goal_description: Optional[str] = None
    priority: str = Field(default="medium", description="critical, high, medium, low")
    target_date: Optional[date] = None
    status: str = Field(default="active", description="active, completed, paused, archived")
    progress_percentage: int = Field(default=0, ge=0, le=100)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ResonantConcept(BaseModel):
    """Resonant Engine固有概念（Hiroaki Model, ERF, Crisis Index等）"""

    id: Optional[UUID] = None
    user_id: str
    concept_type: str = Field(..., description="model, metric, regulation, framework")
    concept_name: str
    definition: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    importance_level: str = Field(default="medium", description="critical, high, medium, low")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserProfileData(BaseModel):
    """完全なユーザープロフィールデータ（集約）"""

    profile: UserProfile
    cognitive_traits: List[CognitiveTrait] = []
    family_members: List[FamilyMember] = []
    goals: List[UserGoal] = []
    resonant_concepts: List[ResonantConcept] = []

    class Config:
        from_attributes = True
