"""Context Assembler - Data Models"""

from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class MemoryLayer(str, Enum):
    """メモリ階層の種類"""

    SYSTEM = "system"
    WORKING = "working"
    SEMANTIC = "semantic"
    SESSION_SUMMARY = "session_summary"
    USER_MESSAGE = "user_message"


class ContextConfig(BaseModel):
    """コンテキスト設定"""

    system_prompt: str = (
        "You are Kana, the external translator for Resonant Engine."
    )
    working_memory_limit: int = Field(default=10, ge=1, le=50)
    semantic_memory_limit: int = Field(default=5, ge=1, le=20)
    max_tokens: int = Field(default=100000, ge=1000)
    token_safety_margin: float = Field(default=0.8, ge=0.5, le=0.95)


class AssemblyOptions(BaseModel):
    """組み立てオプション"""

    working_memory_limit: Optional[int] = None
    semantic_memory_limit: Optional[int] = None
    include_semantic_memory: bool = True
    include_session_summary: bool = True


class ContextMetadata(BaseModel):
    """コンテキストメタデータ"""

    working_memory_count: int = Field(..., ge=0)
    semantic_memory_count: int = Field(..., ge=0)
    has_session_summary: bool
    total_tokens: int = Field(..., ge=0)
    token_limit: int = Field(..., ge=0)
    compression_applied: bool
    assembly_latency_ms: float = Field(..., ge=0)


class AssembledContext(BaseModel):
    """組み立て済みコンテキスト"""

    messages: List[Dict[str, str]]
    metadata: ContextMetadata

    class Config:
        from_attributes = True
