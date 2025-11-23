"""
Memory Lifecycle Models

Pydantic models for memory lifecycle management.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class MemoryScore(BaseModel):
    """メモリスコア情報"""
    memory_id: UUID
    importance_score: float = Field(ge=0.0, le=1.0, description="Importance score (0.0 - 1.0)")
    created_at: datetime
    last_accessed_at: Optional[datetime] = None
    access_count: int = Field(ge=0, default=0)
    decay_applied_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MemoryArchive(BaseModel):
    """アーカイブメモリ"""
    id: Optional[UUID] = None
    user_id: str
    original_memory_id: UUID
    original_content: str
    compressed_summary: str
    compression_method: str = "claude_haiku"
    compressed_at: Optional[datetime] = None
    original_size_bytes: int = Field(ge=0)
    compressed_size_bytes: int = Field(ge=0)
    compression_ratio: float = Field(ge=0.0, le=1.0, description="(original - compressed) / original")
    final_importance_score: float = Field(ge=0.0, le=1.0)
    archive_reason: str = Field(description="Reason: low_importance, capacity_limit, manual")
    retention_until: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class LifecycleEvent(BaseModel):
    """ライフサイクルイベント"""
    id: Optional[UUID] = None
    user_id: str
    memory_id: UUID
    event_type: str = Field(description="Event type: score_update, compress, archive, delete")
    event_details: Optional[Dict[str, Any]] = None
    score_before: Optional[float] = Field(None, ge=0.0, le=1.0)
    score_after: Optional[float] = Field(None, ge=0.0, le=1.0)
    event_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CompressionResult(BaseModel):
    """圧縮結果"""
    archive_id: str
    original_size: int
    compressed_size: int
    compression_ratio: float


class BatchCompressionResult(BaseModel):
    """一括圧縮結果"""
    compressed_count: int = Field(ge=0)
    failed_count: int = Field(ge=0)
    overall_compression_ratio: float = Field(ge=0.0, le=1.0)
    total_original_size: int = Field(ge=0)
    total_compressed_size: int = Field(ge=0)


class MemoryUsage(BaseModel):
    """メモリ使用状況"""
    active_count: int = Field(ge=0, description="Active memories count")
    archive_count: int = Field(ge=0, description="Archived memories count")
    total_count: int = Field(ge=0, description="Total memories count")
    usage_ratio: float = Field(ge=0.0, le=1.0, description="active_count / limit")
    total_size_bytes: int = Field(ge=0, description="Total size in bytes")
    limit: int = Field(ge=0, description="Memory limit")


class CapacityManagementResult(BaseModel):
    """容量管理結果"""
    action: str = Field(description="Action taken: none, auto_compress")
    old_usage: Optional[MemoryUsage] = None
    new_usage: Optional[MemoryUsage] = None
    compress_result: Optional[BatchCompressionResult] = None
