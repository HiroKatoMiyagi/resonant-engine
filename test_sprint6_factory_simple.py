"""Sprint 6: Context Assembler Factory 簡易テスト"""

import sys
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

# context_assembler.factoryを直接インポート
sys.path.insert(0, '/Users/zero/Projects/resonant-engine')

from context_assembler.factory import create_context_assembler, get_database_url
from context_assembler.service import ContextAssemblerService


def test_get_database_url_success():
    """TC-01-1: 環境変数からURL取得成功"""
    import os
    os.environ["DATABASE_URL"] = "postgresql://localhost/test"
    
    url = get_database_url()
    assert url == "postgresql://localhost/test"
    print("✅ TC-01-1 PASS: DATABASE_URL取得成功")


def test_get_database_url_missing():
    """TC-01-2: 環境変数未設定時にエラー"""
    import os
    # DATABASE_URLを削除
    if "DATABASE_URL" in os.environ:
        del os.environ["DATABASE_URL"]
    
    try:
        get_database_url()
        print("❌ TC-01-2 FAIL: エラーが発生しなかった")
    except ValueError as e:
        if "DATABASE_URL" in str(e):
            print("✅ TC-01-2 PASS: DATABASE_URL未設定エラー")
        else:
            print(f"❌ TC-01-2 FAIL: 予期しないエラー: {e}")


async def test_create_context_assembler_with_pool():
    """TC-01: 既存プールでContext Assembler生成"""
    # Mock pool
    mock_pool = AsyncMock()
    
    # Mock repositories and orchestrator
    with patch("context_assembler.factory.MessageRepository") as mock_msg_repo, \
         patch("context_assembler.factory.MemoryRepository") as mock_mem_repo, \
         patch("context_assembler.factory.RetrievalOrchestrator") as mock_retrieval:
        
        # Mock返り値設定
        mock_msg_repo.return_value = MagicMock()
        mock_mem_repo.return_value = MagicMock()
        mock_retrieval.return_value = MagicMock()
        
        ca = await create_context_assembler(pool=mock_pool)
        
        # 検証
        assert isinstance(ca, ContextAssemblerService), "Context Assemblerインスタンス生成失敗"
        assert mock_msg_repo.called, "MessageRepository未呼び出し"
        assert mock_mem_repo.called, "MemoryRepository未呼び出し"
        assert mock_retrieval.called, "RetrievalOrchestrator未呼び出し"
        
        print("✅ TC-01 PASS: Context Assembler生成成功（既存プール）")


async def test_create_context_assembler_with_config():
    """TC-01-3: カスタム設定でContext Assembler生成"""
    from context_assembler.config import ContextConfig
    
    mock_pool = AsyncMock()
    custom_config = ContextConfig(
        working_memory_limit=20,
        semantic_memory_limit=10,
    )
    
    with patch("context_assembler.factory.MessageRepository"), \
         patch("context_assembler.factory.MemoryRepository"), \
         patch("context_assembler.factory.RetrievalOrchestrator"):
        
        ca = await create_context_assembler(pool=mock_pool, config=custom_config)
        
        assert ca is not None, "Context Assembler生成失敗"
        assert ca.config.working_memory_limit == 20, "working_memory_limit設定失敗"
        assert ca.config.semantic_memory_limit == 10, "semantic_memory_limit設定失敗"
        
        print("✅ TC-01-3 PASS: カスタム設定でContext Assembler生成成功")


async def test_create_context_assembler_import_error():
    """TC-03: 依存関係インポート失敗時にエラー"""
    mock_pool = AsyncMock()
    
    # MessageRepositoryのインポート失敗を模擬
    with patch("context_assembler.factory.MessageRepository", side_effect=ImportError("Test error")):
        try:
            await create_context_assembler(pool=mock_pool)
            print("❌ TC-03 FAIL: ImportErrorが発生しなかった")
        except ImportError as e:
            if "Memory Store" in str(e):
                print("✅ TC-03 PASS: Memory Store依存関係エラー検出")
            else:
                print(f"❌ TC-03 FAIL: 予期しないエラー: {e}")


async def test_create_context_assembler_retrieval_import_error():
    """TC-03-2: Retrieval Orchestratorインポート失敗時にエラー"""
    mock_pool = AsyncMock()
    
    with patch("context_assembler.factory.MessageRepository"), \
         patch("context_assembler.factory.MemoryRepository"), \
         patch("context_assembler.factory.RetrievalOrchestrator", side_effect=ImportError("Test error")):
        try:
            await create_context_assembler(pool=mock_pool)
            print("❌ TC-03-2 FAIL: ImportErrorが発生しなかった")
        except ImportError as e:
            if "Retrieval Orchestrator" in str(e):
                print("✅ TC-03-2 PASS: Retrieval Orchestrator依存関係エラー検出")
            else:
                print(f"❌ TC-03-2 FAIL: 予期しないエラー: {e}")


async def main():
    """全テストを実行"""
    print("=" * 70)
    print("Sprint 6: Context Assembler Factory 簡易テスト")
    print("=" * 70)
    print()
    
    # 同期テスト
    test_get_database_url_success()
    test_get_database_url_missing()
    print()
    
    # 非同期テスト
    await test_create_context_assembler_with_pool()
    await test_create_context_assembler_with_config()
    await test_create_context_assembler_import_error()
    await test_create_context_assembler_retrieval_import_error()
    
    print()
    print("=" * 70)
    print("テスト完了")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
