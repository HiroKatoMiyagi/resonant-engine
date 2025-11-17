"""
Memory Store Data Models

Pydantic models for memory storage and retrieval.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MemoryType(str, Enum):
    """記憶タイプ"""
    WORKING = "working"  # 24時間の作業記憶
    LONGTERM = "longterm"  # 長期記憶


class SourceType(str, Enum):
    """記憶ソース"""
    INTENT = "intent"
    THOUGHT = "thought"
    CORRECTION = "correction"
    DECISION = "decision"


class MemoryCreate(BaseModel):
    """記憶作成リクエスト"""
    content: str = Field(..., min_length=1, max_length=100000)
    memory_type: MemoryType
    source_type: Optional[SourceType] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    expires_at: Optional[datetime] = None

    class Config:
        use_enum_values = False


class MemoryRecord(BaseModel):
    """データベースに保存される記憶レコード"""
    id: int
    content: str
    embedding: List[float]  # 1536次元ベクトル
    memory_type: MemoryType
    source_type: Optional[SourceType] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    is_archived: bool = False

    class Config:
        use_enum_values = False


class MemoryResult(BaseModel):
    """記憶検索結果"""
    id: int
    content: str
    memory_type: MemoryType
    source_type: Optional[SourceType] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    similarity: float = Field(..., ge=0.0, le=1.0)
    created_at: datetime

    class Config:
        use_enum_values = False
        from_attributes = True


class MemorySearchQuery(BaseModel):
    """メモリ検索クエリ"""
    query: str = Field(..., min_length=1)
    memory_type: Optional[MemoryType] = None
    source_type: Optional[SourceType] = None
    limit: int = Field(default=10, ge=1, le=1000)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    include_archived: bool = False

    # Metadata filters
    tags: Optional[List[str]] = None
    importance_min: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    importance_max: Optional[float] = Field(default=None, ge=0.0, le=1.0)

    # Date filters
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None

    class Config:
        use_enum_values = False


class MemoryStoreConfig(BaseModel):
    """Memory Store設定"""
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    similarity_threshold: float = 0.7
    working_memory_ttl_hours: int = 24
    cache_enabled: bool = True
    max_cache_size: int = 10000
