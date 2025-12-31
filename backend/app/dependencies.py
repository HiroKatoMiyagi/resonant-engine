"""Dependency injection for Backend API"""

from typing import AsyncGenerator, Optional
import asyncpg
import os
from functools import lru_cache

from app.database import db
from app.services.contradiction.detector import ContradictionDetector
from app.services.dashboard.service import DashboardService
from app.services.dashboard.repository import PostgresDashboardRepository
from app.services.intent.bridge_set import BridgeSet
from app.services.intent.reeval import ReEvalClient
from app.services.intent.data_bridge import DataBridge
from app.services.intent.ai_bridge import AIBridge
from app.services.intent.feedback_bridge import FeedbackBridge
from app.integrations.audit_logger import AuditLogger
from memory_store.service import MemoryStoreService
from memory_lifecycle.capacity_manager import CapacityManager
from memory_lifecycle.compression_service import MemoryCompressionService


async def get_db_pool() -> asyncpg.Pool:
    """データベース接続プール取得"""
    return db.pool


@lru_cache
def get_contradiction_detector() -> ContradictionDetector:
    """Contradiction Detector取得（シングルトン）"""
    # Note: poolは実行時に取得する必要があるため、ここでは初期化のみ
    return ContradictionDetector()


async def get_memory_service() -> MemoryStoreService:
    """Memory Store Service取得"""
    pool = await get_db_pool()
    from memory_store.repository import InMemoryRepository
    from memory_store.embedding import EmbeddingService
    
    # テスト用にInMemoryRepositoryを使用
    # 本番環境ではPostgreSQL実装が必要
    repository = InMemoryRepository()
    embedding_service = EmbeddingService()
    
    return MemoryStoreService(
        repository=repository,
        embedding_service=embedding_service
    )


async def get_capacity_manager() -> CapacityManager:
    """Capacity Manager取得"""
    pool = await get_db_pool()
    compression_service = await get_compression_service()
    from memory_lifecycle.importance_scorer import ImportanceScorer
    scorer = ImportanceScorer(pool=pool)
    return CapacityManager(
        pool=pool,
        compression_service=compression_service,
        scorer=scorer
    )


async def get_compression_service() -> MemoryCompressionService:
    """Memory Compression Service取得"""
    pool = await get_db_pool()
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")
    return MemoryCompressionService(pool=pool, anthropic_api_key=anthropic_api_key)


@lru_cache
def get_dashboard_service() -> DashboardService:
    """Dashboard Service取得（シングルトン）"""
    database_url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_DSN")
    if not database_url:
        raise ValueError("DATABASE_URL or POSTGRES_DSN environment variable is not set")
    repository = PostgresDashboardRepository(database_url)
    return DashboardService(repository)


# ===== Bridge Component Factories =====

def create_data_bridge(bridge_type: Optional[str] = None) -> DataBridge:
    """DataBridge生成"""
    from app.integrations import MockDataBridge, PostgresDataBridge
    
    bridge_key = (bridge_type or os.getenv("DATA_BRIDGE_TYPE", "mock")).lower()
    if bridge_key in {"postgresql", "postgres", "pg"}:
        return PostgresDataBridge()
    if bridge_key == "mock":
        return MockDataBridge()
    raise ValueError(f"Unsupported DATA_BRIDGE_TYPE: {bridge_key}")


def create_ai_bridge(bridge_type: Optional[str] = None) -> AIBridge:
    """AIBridge生成"""
    from app.integrations import KanaAIBridge, MockAIBridge
    
    bridge_key = (bridge_type or os.getenv("AI_BRIDGE_TYPE", "kana")).lower()
    if bridge_key in {"kana", "claude"}:
        return KanaAIBridge()
    if bridge_key == "mock":
        return MockAIBridge()
    raise ValueError(f"Unsupported AI_BRIDGE_TYPE: {bridge_key}")


async def create_ai_bridge_with_memory(
    bridge_type: Optional[str] = None,
    pool: Optional[asyncpg.Pool] = None,
) -> AIBridge:
    """Context Assembler統合版のAI Bridge生成"""
    from context_assembler.factory import create_context_assembler
    from app.integrations import KanaAIBridge, MockAIBridge
    import warnings
    
    bridge_key = (bridge_type or os.getenv("AI_BRIDGE_TYPE", "kana")).lower()
    
    if bridge_key in {"kana", "claude"}:
        try:
            context_assembler = await create_context_assembler(pool=pool)
        except (ConnectionError, ValueError, ImportError) as e:
            warnings.warn(
                f"Context Assembler initialization failed: {e}. "
                f"Falling back to KanaAIBridge without context memory."
            )
            return KanaAIBridge()
        return KanaAIBridge(context_assembler=context_assembler)
    
    if bridge_key == "mock":
        return MockAIBridge()
    
    raise ValueError(f"Unsupported AI_BRIDGE_TYPE: {bridge_key}")


def create_feedback_bridge(
    bridge_type: Optional[str] = None,
    reeval_client: Optional[ReEvalClient] = None,
) -> FeedbackBridge:
    """FeedbackBridge生成"""
    from app.integrations import MockFeedbackBridge, YunoFeedbackBridge
    
    bridge_key = (bridge_type or os.getenv("FEEDBACK_BRIDGE_TYPE", "mock")).lower()
    if bridge_key == "yuno":
        return YunoFeedbackBridge(reeval_client=reeval_client)
    if bridge_key == "mock":
        return MockFeedbackBridge(reeval_client=reeval_client)
    raise ValueError(f"Unsupported FEEDBACK_BRIDGE_TYPE: {bridge_key}")


@lru_cache
def get_audit_logger() -> AuditLogger:
    """AuditLogger取得（シングルトン）"""
    from app.integrations import PostgresAuditLogger, MockAuditLogger
    
    logger_type = os.getenv("AUDIT_LOGGER_TYPE", "postgres").lower()
    if logger_type in {"postgresql", "postgres", "pg"}:
        return PostgresAuditLogger()
    if logger_type == "mock":
        return MockAuditLogger()
    raise ValueError(f"Unsupported AUDIT_LOGGER_TYPE: {logger_type}")


def create_bridge_set(
    data_bridge: Optional[str] = None,
    ai_bridge: Optional[str] = None,
    feedback_bridge: Optional[str] = None,
    audit_logger: Optional[str] = None,
) -> BridgeSet:
    """BridgeSet生成"""
    data = create_data_bridge(data_bridge)
    ai = create_ai_bridge(ai_bridge)
    audit = get_audit_logger()
    reeval_client = ReEvalClient(data, audit)
    feedback = create_feedback_bridge(feedback_bridge, reeval_client=reeval_client)
    feedback.attach_reeval_client(reeval_client)
    return BridgeSet(data=data, ai=ai, feedback=feedback, audit=audit)


async def get_bridge_set() -> BridgeSet:
    """BridgeSet取得（Re-evaluation用）"""
    return create_bridge_set()


# ========================================
# Sprint 12 Dependencies
# ========================================

from app.services.term_drift.detector import TermDriftDetector
from app.services.temporal_constraint.checker import TemporalConstraintChecker
from app.services.file_modification.service import FileModificationService

@lru_cache
def get_term_drift_detector() -> TermDriftDetector:
    """Term Drift Detector取得"""
    # Note: db.pool might not be available if not running in async context where db is initialized
    # But for dependencies, we assume app startup has happened or db is accessible.
    # However, db.pool is an asyncpg.Pool.
    # We should ensure db is imported correctly.
    return TermDriftDetector(db.pool)

@lru_cache
def get_temporal_constraint_checker() -> TemporalConstraintChecker:
    """Temporal Constraint Checker取得"""
    return TemporalConstraintChecker(db.pool)


@lru_cache
def get_file_modification_service() -> FileModificationService:
    """File Modification Service取得（シングルトン）"""
    constraint_checker = get_temporal_constraint_checker()
    return FileModificationService(
        pool=db.pool,
        constraint_checker=constraint_checker
    )
