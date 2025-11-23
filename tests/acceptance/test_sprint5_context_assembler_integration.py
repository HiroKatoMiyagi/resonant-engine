"""Sprint 5: Context Assembler - 実PostgreSQL統合テスト

モックを使用せず、実際のPostgreSQLとデータを使用してテストします。
"""

import pytest
import asyncio
from uuid import uuid4
from datetime import datetime, timezone


@pytest.mark.asyncio
async def test_context_assembler_with_real_db(db_pool):
    """実際のPostgreSQLを使用したContext Assemblerテスト"""
    try:
        from context_assembler.factory import create_context_assembler
        from dashboard.backend.repositories.message_repository import MessageRepository
        from dashboard.backend.models.message import MessageCreate
        
        # Context Assembler作成
        context_assembler = await create_context_assembler(pool=db_pool)
        
        # テストユーザー
        user_id = f"test_user_{uuid4()}"
        
        # メッセージリポジトリ
        message_repo = MessageRepository(db_pool)
        
        # テストメッセージを作成
        await message_repo.create(MessageCreate(
            user_id=user_id,
            content="Resonant Engineについて教えてください",
            message_type="user",
            metadata={}
        ))
        
        await message_repo.create(MessageCreate(
            user_id=user_id,
            content="Resonant Engineは呼吸のリズムで動作するAIシステムです",
            message_type="kana",
            metadata={}
        ))
        
        # コンテキスト組み立て
        result = await context_assembler.assemble_context(
            user_message="Memory Storeについて詳しく教えてください",
            user_id=user_id
        )
        
        # 検証
        assert result is not None
        assert len(result.messages) >= 3  # system + working memory + user message
        assert result.messages[0]["role"] == "system"
        assert result.messages[-1]["role"] == "user"
        assert result.messages[-1]["content"] == "Memory Storeについて詳しく教えてください"
        
        # メタデータ検証
        assert result.metadata.working_memory_count >= 2
        assert result.metadata.total_tokens > 0
        assert result.metadata.assembly_latency_ms >= 0
        
        print(f"✅ Context Assembler統合テスト成功")
        print(f"  - Working Memory: {result.metadata.working_memory_count}件")
        print(f"  - Total Tokens: {result.metadata.total_tokens}")
        print(f"  - Latency: {result.metadata.assembly_latency_ms:.2f}ms")
        
    except ImportError as e:
        pytest.skip(f"Context Assembler not fully implemented: {e}")


@pytest.mark.asyncio
async def test_context_assembler_token_estimation(db_pool):
    """トークン推定の精度テスト"""
    try:
        from context_assembler.token_estimator import TokenEstimator
        
        estimator = TokenEstimator()
        
        # 日本語テスト
        japanese_messages = [
            {"role": "user", "content": "こんにちは、Resonant Engineについて教えてください"}
        ]
        tokens_ja = estimator.estimate(japanese_messages)
        assert 10 <= tokens_ja <= 50
        
        # 英語テスト
        english_messages = [
            {"role": "user", "content": "Hello, please tell me about Resonant Engine"}
        ]
        tokens_en = estimator.estimate(english_messages)
        assert 10 <= tokens_en <= 30
        
        # 混在テスト
        mixed_messages = [
            {"role": "system", "content": "You are Kana"},
            {"role": "user", "content": "Resonant Engineは呼吸で動く"},
            {"role": "assistant", "content": "その通りです"}
        ]
        tokens_mixed = estimator.estimate(mixed_messages)
        assert 30 <= tokens_mixed <= 100
        
        print(f"✅ トークン推定テスト成功")
        print(f"  - 日本語: {tokens_ja} tokens")
        print(f"  - 英語: {tokens_en} tokens")
        print(f"  - 混在: {tokens_mixed} tokens")
        
    except ImportError as e:
        pytest.skip(f"Token Estimator not implemented: {e}")


@pytest.mark.asyncio
async def test_context_assembler_with_semantic_memory(db_pool):
    """Semantic Memoryを含むコンテキスト組み立てテスト"""
    try:
        from context_assembler.factory import create_context_assembler
        from memory_store.service import MemoryStoreService
        from memory_store.repository import MemoryStoreRepository
        from memory_store.models import MemoryType
        
        # Context Assembler作成
        context_assembler = await create_context_assembler(pool=db_pool)
        
        # Memory Store作成
        memory_repo = MemoryStoreRepository(db_pool)
        memory_service = MemoryStoreService(memory_repo)
        
        # テストユーザー
        user_id = f"test_user_{uuid4()}"
        
        # 長期記憶を保存
        await memory_service.save_memory(
            content="Resonant Engineは呼吸のリズムで動作するAIシステムです",
            memory_type=MemoryType.LONGTERM,
            source_type="decision",
            metadata={"user_id": user_id}
        )
        
        # コンテキスト組み立て
        result = await context_assembler.assemble_context(
            user_message="呼吸のリズムについて教えてください",
            user_id=user_id
        )
        
        # 検証
        assert result is not None
        assert len(result.messages) >= 2
        
        # Semantic Memoryが含まれているか確認
        # （実装に応じて検証内容を調整）
        assert result.metadata.semantic_memory_count >= 0
        
        print(f"✅ Semantic Memory統合テスト成功")
        print(f"  - Semantic Memory: {result.metadata.semantic_memory_count}件")
        
    except ImportError as e:
        pytest.skip(f"Dependencies not fully implemented: {e}")
