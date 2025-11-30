"""Dependency injection for Backend API"""

from typing import AsyncGenerator
import asyncpg
import os
from app.database import db
from bridge.contradiction.detector import ContradictionDetector
from memory_store.service import MemoryStoreService
from memory_lifecycle.capacity_manager import CapacityManager
from memory_lifecycle.compression_service import MemoryCompressionService
from bridge.factory.bridge_factory import BridgeFactory
from bridge.dashboard import DashboardService, PostgresDashboardRepository


async def get_db_pool() -> asyncpg.Pool:
    """データベース接続プール取得"""
    return db.pool


async def get_contradiction_detector() -> ContradictionDetector:
    """Contradiction Detector取得"""
    pool = await get_db_pool()
    return ContradictionDetector(pool=pool)


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
    scorer = ImportanceScorer(pool=pool)  # ← 修正: poolパラメータを追加
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


async def get_bridge_set():
    """BridgeSet取得（Re-evaluation用）"""
    return BridgeFactory.create_bridge_set()


async def get_dashboard_service() -> DashboardService:
    """Dashboard Service取得"""
    # シングルトンパターンで実装
    service = getattr(get_dashboard_service, "_instance", None)
    if service is None:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is not set")
        repository = PostgresDashboardRepository(database_url)
        service = DashboardService(repository)
        setattr(get_dashboard_service, "_instance", service)
    return service
