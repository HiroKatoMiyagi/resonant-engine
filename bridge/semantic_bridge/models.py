"""
Semantic Bridge Data Models

Pydantic models for memory units, event contexts, and inference results.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class MemoryType(str, Enum):
    """メモリタイプ（memory_itemスキーマと一致）"""
    SESSION_SUMMARY = "session_summary"
    DAILY_REFLECTION = "daily_reflection"
    PROJECT_MILESTONE = "project_milestone"
    RESONANT_REGULATION = "resonant_regulation"
    DESIGN_NOTE = "design_note"
    CRISIS_LOG = "crisis_log"


class EmotionState(str, Enum):
    """感情状態"""
    CALM = "calm"
    FOCUSED = "focused"
    STRESSED = "stressed"
    CRISIS = "crisis"
    EXCITED = "excited"
    NEUTRAL = "neutral"


class MemoryUnit(BaseModel):
    """意味的メモリユニット - Event to Memoryの変換結果"""
    id: UUID = Field(default_factory=uuid4)
    user_id: str = "hiroki"  # Phase 4までは固定
    project_id: Optional[str] = None
    type: MemoryType

    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    content_raw: Optional[str] = None  # 元のIntent文面

    tags: List[str] = Field(default_factory=list)
    ci_level: Optional[int] = Field(default=None, ge=0, le=100)
    emotion_state: Optional[EmotionState] = None

    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic model configuration"""
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat(),
        }
        use_enum_values = False


class EventContext(BaseModel):
    """イベントの文脈情報 - 処理対象のイベント"""
    intent_id: UUID
    intent_text: str = Field(..., min_length=1)
    intent_type: str
    session_id: Optional[UUID] = None

    crisis_index: Optional[int] = Field(default=None, ge=0, le=100)
    timestamp: datetime

    # Bridge処理情報
    bridge_result: Optional[Dict[str, Any]] = None

    # Kana応答情報
    kana_response: Optional[str] = None

    # その他の文脈
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic model configuration"""
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat(),
        }


class InferenceResult(BaseModel):
    """推論結果 - タイプとプロジェクトの自動推論結果"""
    memory_type: MemoryType
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str  # 推論理由

    project_id: Optional[str] = None
    project_confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    tags: List[str] = Field(default_factory=list)
    emotion_state: Optional[EmotionState] = None

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """タグの重複を除去"""
        return list(set(v))


class TypeInferenceRule(BaseModel):
    """タイプ推論ルール - パターンマッチング用"""
    pattern: str  # 正規表現またはキーワード
    memory_type: MemoryType
    priority: int = Field(default=0, ge=0, le=100)
    description: str

    class Config:
        """Pydantic model configuration"""
        use_enum_values = False


class MemorySearchQuery(BaseModel):
    """メモリ検索クエリ - シンボリック検索用"""
    user_id: str = "hiroki"

    # プロジェクトフィルタ
    project_id: Optional[str] = None
    project_ids: Optional[List[str]] = None

    # タイプフィルタ
    type: Optional[MemoryType] = None
    types: Optional[List[MemoryType]] = None

    # タグフィルタ
    tags: Optional[List[str]] = None
    tag_mode: str = Field(default="any", pattern="^(any|all)$")  # "any" or "all"

    # 時間範囲
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None

    # CI Levelフィルタ
    ci_level_min: Optional[int] = Field(default=None, ge=0, le=100)
    ci_level_max: Optional[int] = Field(default=None, ge=0, le=100)

    # 感情状態フィルタ
    emotion_states: Optional[List[EmotionState]] = None

    # テキスト検索（LIKE検索）
    text_query: Optional[str] = None

    # ページング
    limit: int = Field(default=10, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)

    # ソート
    sort_by: str = Field(default="created_at", pattern="^(created_at|ci_level|updated_at)$")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")

    @field_validator("ci_level_max")
    @classmethod
    def validate_ci_level_range(cls, v: Optional[int], info) -> Optional[int]:
        """CI Level範囲のバリデーション"""
        if v is not None and info.data.get("ci_level_min") is not None:
            if v < info.data["ci_level_min"]:
                raise ValueError("ci_level_max must be >= ci_level_min")
        return v

    class Config:
        """Pydantic model configuration"""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
        use_enum_values = False
