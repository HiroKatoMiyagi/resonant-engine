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
        from memory_store.repository import MessageRepository, MemoryRepository
    except ImportError as e:
        raise ImportError(
            "Memory Store repositories not found. "
            "Please implement memory_store/repository.py or use Mock."
        ) from e

    message_repo = MessageRepository(pool)
    memory_repo = MemoryRepository(pool)

    # 3. Retrieval Orchestrator初期化
    try:
        from retrieval.orchestrator import RetrievalOrchestrator
    except ImportError as e:
        raise ImportError(
            "Retrieval Orchestrator not found. "
            "Please implement retrieval/orchestrator.py or use Mock."
        ) from e

    retrieval = RetrievalOrchestrator(memory_repo=memory_repo)

    # 4. Context Assembler初期化
    return ContextAssemblerService(
        message_repo=message_repo,
        retrieval=retrieval,
        config=config or get_default_config(),
    )
