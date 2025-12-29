from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum

# ========================================
# Enums
# ========================================

class TermCategory(str, Enum):
    DOMAIN_OBJECT = "domain_object"  # Intent, Memory, Bridge等
    TECHNICAL = "technical"           # 認証, API, データベース等
    PROCESS = "process"               # Sprint, Deploy, Test等
    CUSTOM = "custom"                 # ユーザー定義

class DriftType(str, Enum):
    EXPANSION = "expansion"           # フィールド追加等
    CONTRACTION = "contraction"       # フィールド削除等
    SEMANTIC_SHIFT = "semantic_shift" # 意味の変化
    CONTEXT_CHANGE = "context_change" # 使用コンテキストの変化

class DriftStatus(str, Enum):
    PENDING = "pending"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"

# ========================================
# Term Drift Models
# ========================================

class TermDefinition(BaseModel):
    """用語定義"""
    id: Optional[UUID] = None
    user_id: str
    term_name: str
    term_category: TermCategory = TermCategory.CUSTOM
    definition_text: str
    definition_context: Optional[str] = None
    definition_source: Optional[str] = None
    structured_definition: Optional[Dict[str, Any]] = None
    version: int = 1
    is_current: bool = True
    defined_at: Optional[datetime] = None

class TermDrift(BaseModel):
    """検出されたドリフト"""
    id: Optional[UUID] = None
    user_id: str
    term_name: str
    original_definition_id: Optional[UUID] = None
    new_definition_id: Optional[UUID] = None
    drift_type: DriftType
    confidence_score: float = Field(ge=0.0, le=1.0)
    change_summary: str
    impact_analysis: Optional[Dict[str, Any]] = None
    status: DriftStatus = DriftStatus.PENDING
    detected_at: Optional[datetime] = None

class TermDriftResolution(BaseModel):
    """ドリフト解決リクエスト"""
    resolution_action: str  # 'intentional_change', 'rollback', 'migration_needed'
    resolution_note: str = Field(min_length=10)
    resolved_by: str

class AnalyzeRequest(BaseModel):
    """分析リクエスト"""
    user_id: str
    text: str
    source: str
