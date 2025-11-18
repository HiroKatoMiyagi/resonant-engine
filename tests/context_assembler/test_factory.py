"""Context Assembler Factory単体テスト"""

import pytest
import asyncpg
from unittest.mock import AsyncMock, MagicMock, patch

from context_assembler.factory import (
    create_context_assembler,
    get_database_url,
)
from context_assembler.service import ContextAssemblerService


def test_get_database_url_success(monkeypatch):
    """環境変数からURL取得成功 (TC-01-1)"""
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/test")
    url = get_database_url()
    assert url == "postgresql://localhost/test"


def test_get_database_url_missing(monkeypatch):
    """環境変数未設定時にエラー (TC-01-2)"""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValueError, match="DATABASE_URL"):
        get_database_url()


@pytest.mark.asyncio
async def test_create_context_assembler_with_pool():
    """既存プールでContext Assembler生成 (TC-01)"""
    # Mock pool
    mock_pool = AsyncMock(spec=asyncpg.Pool)

    # Mock repositories and orchestrator
    with patch("context_assembler.factory.MessageRepository") as mock_msg_repo, \
         patch("context_assembler.factory.MemoryRepository") as mock_mem_repo, \
         patch("context_assembler.factory.RetrievalOrchestrator") as mock_retrieval:

        ca = await create_context_assembler(pool=mock_pool)

        # 検証
        assert isinstance(ca, ContextAssemblerService)
        mock_msg_repo.assert_called_once_with(mock_pool)
        mock_mem_repo.assert_called_once_with(mock_pool)
        mock_retrieval.assert_called_once()


@pytest.mark.asyncio
async def test_create_context_assembler_with_config():
    """カスタム設定でContext Assembler生成 (TC-01-3)"""
    from context_assembler.config import ContextConfig

    mock_pool = AsyncMock(spec=asyncpg.Pool)
    custom_config = ContextConfig(
        working_memory_limit=20,
        semantic_memory_limit=10,
    )

    with patch("context_assembler.factory.MessageRepository"), \
         patch("context_assembler.factory.MemoryRepository"), \
         patch("context_assembler.factory.RetrievalOrchestrator"):

        ca = await create_context_assembler(pool=mock_pool, config=custom_config)

        assert ca is not None
        assert ca.config.working_memory_limit == 20
        assert ca.config.semantic_memory_limit == 10


@pytest.mark.asyncio
async def test_create_context_assembler_import_error():
    """依存関係インポート失敗時にエラー (TC-03)"""
    mock_pool = AsyncMock(spec=asyncpg.Pool)

    # MessageRepositoryのインポート失敗を模擬
    with patch("context_assembler.factory.MessageRepository", side_effect=ImportError("Test error")):
        with pytest.raises(ImportError, match="Memory Store"):
            await create_context_assembler(pool=mock_pool)


@pytest.mark.asyncio
async def test_create_context_assembler_retrieval_import_error():
    """Retrieval Orchestratorインポート失敗時にエラー (TC-03-2)"""
    mock_pool = AsyncMock(spec=asyncpg.Pool)

    with patch("context_assembler.factory.MessageRepository"), \
         patch("context_assembler.factory.MemoryRepository"), \
         patch("context_assembler.factory.RetrievalOrchestrator", side_effect=ImportError("Test error")):
        with pytest.raises(ImportError, match="Retrieval Orchestrator"):
            await create_context_assembler(pool=mock_pool)


@pytest.mark.asyncio
async def test_create_context_assembler_connection_error(monkeypatch):
    """DB接続失敗時にエラー (TC-02)"""
    monkeypatch.setenv("DATABASE_URL", "postgresql://invalid:5432/test")

    # create_poolが失敗するようにmock
    with patch("asyncpg.create_pool", side_effect=Exception("Connection failed")):
        with pytest.raises(ConnectionError, match="Failed to create database pool"):
            await create_context_assembler()


@pytest.mark.asyncio
async def test_create_context_assembler_creates_pool_when_none():
    """poolがNoneの場合に新規プールを作成 (TC-01-4)"""
    with patch("context_assembler.factory.get_database_url", return_value="postgresql://localhost/test"), \
         patch("asyncpg.create_pool") as mock_create_pool, \
         patch("context_assembler.factory.MessageRepository"), \
         patch("context_assembler.factory.MemoryRepository"), \
         patch("context_assembler.factory.RetrievalOrchestrator"):

        mock_pool = AsyncMock(spec=asyncpg.Pool)
        mock_create_pool.return_value = mock_pool

        ca = await create_context_assembler(pool=None)

        # プール作成が呼ばれたことを確認
        mock_create_pool.assert_called_once_with(
            "postgresql://localhost/test",
            min_size=2,
            max_size=10,
            timeout=30,
        )
        assert ca is not None
