"""Context Assembler Factory - 依存関係注入層"""

import asyncpg
import os
from typing import Optional

from context_assembler.service import ContextAssemblerService
from context_assembler.config import get_default_config, ContextConfig


def get_database_url() -> str:
    """
    環境変数からデータベースURLを取得

    Returns:
        str: PostgreSQL接続URL

    Raises:
        ValueError: DATABASE_URL環境変数が未設定
    """
    url = os.getenv("DATABASE_URL")
    if not url:
        raise ValueError(
            "DATABASE_URL environment variable is not set. "
            "Example: postgresql://user:password@localhost:5432/resonant_engine"
        )
    return url


async def create_context_assembler(
    pool: Optional[asyncpg.Pool] = None,
    config: Optional[ContextConfig] = None,
) -> ContextAssemblerService:
    """
    Context Assemblerインスタンスを生成

    Args:
        pool: PostgreSQL接続プール（Noneの場合は新規作成）
        config: Context設定（Noneの場合はデフォルト）

    Returns:
        ContextAssemblerService: 初期化済みインスタンス

    Raises:
        ConnectionError: データベース接続失敗
        ValueError: 依存関係の初期化失敗
        ImportError: 必須モジュール未インストール

    Example:
        >>> pool = await asyncpg.create_pool("postgresql://...")
        >>> ca = await create_context_assembler(pool=pool)
        >>> context = await ca.assemble_context(
        ...     user_message="Memory Storeについて教えて",
        ...     user_id="hiroki"
        ... )
    """
    # 1. データベース接続プール
    if pool is None:
        database_url = get_database_url()
        try:
            pool = await asyncpg.create_pool(
                database_url,
                min_size=2,
                max_size=10,
                timeout=30,
            )
        except Exception as e:
            raise ConnectionError(f"Failed to create database pool: {e}") from e

    # 2. リポジトリ初期化
    try:
        from backend.app.repositories.message_repo import MessageRepository
        from memory_store.repository import MemoryRepository
        from app.services.memory.repositories import SessionRepository
    except ImportError as e:
        raise ImportError(
            "Required repositories not found. "
            "Please implement repositories or use Mock."
        ) from e

    message_repo = MessageRepository(pool)
    memory_repo = MemoryRepository(pool)
    session_repo = SessionRepository(pool)

    # 3. Retrieval Orchestrator初期化
    try:
        from retrieval.orchestrator import RetrievalOrchestrator
    except ImportError as e:
        raise ImportError(
            "Retrieval Orchestrator not found. "
            "Please implement retrieval/orchestrator.py or use Mock."
        ) from e

    retrieval = RetrievalOrchestrator(memory_repo=memory_repo)

    # 4. Sprint 7: Session Summary Repository初期化
    session_summary_repo = None
    try:
        from memory_store.session_summary_repository import SessionSummaryRepository
        session_summary_repo = SessionSummaryRepository(pool)
        import logging
        logging.info("✅ Session Summary Repository initialized")
    except ImportError:
        import logging
        logging.warning("Session Summary Repository not available")

    # 5. Sprint 8: User Profile Context Provider初期化
    profile_provider = None
    try:
        from user_profile.repository import UserProfileRepository
        from user_profile.context_provider import ProfileContextProvider
        profile_repo = UserProfileRepository(pool)
        profile_provider = ProfileContextProvider(profile_repo)
        import logging
        logging.info("✅ User Profile Context Provider initialized")
    except ImportError as e:
        import logging
        logging.warning(f"User Profile Context Provider not available: {e}")

    # 6. Context Assembler初期化
    return ContextAssemblerService(
        retrieval_orchestrator=retrieval,
        message_repository=message_repo,
        session_repository=session_repo,
        config=config or get_default_config(),
        session_summary_repository=session_summary_repo,
        profile_context_provider=profile_provider,
    )
