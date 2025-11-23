"""Sprint 5: Context Assembler — 受け入れテスト

受け入れテスト仕様書: docs/02_components/memory_system/test/sprint5_acceptance_test_spec.md

実装内容:
- Working Memory取得
- Semantic Memory取得
- Session Summary取得
- メッセージリスト構築
- トークン数推定・圧縮
- Context Validator検証
- KanaAIBridge統合
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, Mock, patch


@pytest.mark.asyncio
class TestSprint5ContextAssemblerAcceptance:
    """Sprint 5 受け入れテスト: Context Assembler実装"""

    async def test_tc_01_fetch_working_memory(self, db_pool):
        """TC-01: Working Memory取得テスト"""
        try:
            from context_assembler.service import ContextAssembler
            from dashboard.backend.repositories.message_repository import MessageRepository
            from dashboard.backend.models.message import MessageCreate
            
            # テストデータ作成
            message_repo = MessageRepository(db_pool)
            user_id = f"test_user_{uuid4()}"
            
            # 15件のメッセージを作成
            for i in range(15):
                await message_repo.create(MessageCreate(
                    user_id=user_id,
                    content=f"Message {i}",
                    message_type="user" if i % 2 == 0 else "kana",
                    metadata={}
                ))
            
            # Context Assembler初期化
            context_assembler = ContextAssembler(db_pool)
            
            # Working Memory取得
            working_memory = await context_assembler._fetch_working_memory(
                user_id=user_id,
                limit=10
            )
            
            # 検証
            assert len(working_memory) == 10
            assert working_memory[0].content == "Message 5"  # 古い方から
            assert working_memory[-1].content == "Message 14"  # 新しい方
            
        except ImportError:
            pytest.skip("Context Assembler not implemented yet")

    async def test_tc_02_fetch_semantic_memory(self, db_pool):
        """TC-02: Semantic Memory取得テスト"""
        try:
            from context_assembler.service import ContextAssembler
            from memory_store.service import MemoryStoreService
            from memory_store.repository import MemoryStoreRepository
            from memory_store.models import MemoryType
            
            # Memory Store初期化
            memory_repo = MemoryStoreRepository(db_pool)
            memory_store = MemoryStoreService(memory_repo)
            
            # テストデータ作成
            await memory_store.save_memory(
                "Resonant Engineは呼吸のリズムで動作する",
                MemoryType.LONGTERM,
                source_type="decision"
            )
            await memory_store.save_memory(
                "呼吸モデルは6つのフェーズからなる",
                MemoryType.LONGTERM,
                source_type="thought"
            )
            await memory_store.save_memory(
                "全く関係ない記憶",
                MemoryType.LONGTERM
            )
            
            # Context Assembler初期化
            context_assembler = ContextAssembler(db_pool)
            
            # Semantic Memory取得
            semantic_memory = await context_assembler._fetch_semantic_memory(
                query="呼吸のリズムについて教えて",
                limit=5
            )
            
            # 検証
            assert len(semantic_memory) > 0
            assert semantic_memory[0].similarity > 0.5
            assert "呼吸" in semantic_memory[0].content or "リズム" in semantic_memory[0].content
            
        except ImportError:
            pytest.skip("Context Assembler or Memory Store not implemented yet")

    async def test_tc_04_build_messages(self, db_pool):
        """TC-04: メッセージリスト構築テスト"""
        try:
            from context_assembler.service import ContextAssembler
            from memory_store.models import MemoryResult, MemoryType
            from dashboard.backend.models.message import MessageResponse
            
            context_assembler = ContextAssembler(db_pool)
            
            # モックデータ
            memory_layers = {
                "session_summary": "Previous discussion about Resonant Engine",
                "semantic": [
                    MemoryResult(
                        id=1,
                        content="Resonant Engineは呼吸で動く",
                        memory_type=MemoryType.LONGTERM,
                        similarity=0.9,
                        created_at=datetime.now(timezone.utc)
                    )
                ],
                "working": [
                    MessageResponse(
                        id=uuid4(),
                        user_id="test",
                        content="こんにちは",
                        message_type="user",
                        metadata={},
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc)
                    ),
                    MessageResponse(
                        id=uuid4(),
                        user_id="test",
                        content="こんにちは！",
                        message_type="kana",
                        metadata={},
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc)
                    )
                ]
            }
            
            user_message = "Memory Storeについて教えて"
            
            # メッセージ構築
            messages = context_assembler._build_messages(memory_layers, user_message)
            
            # 検証
            assert len(messages) >= 5
            assert messages[0]["role"] == "system"
            assert "Previous discussion" in messages[0]["content"]
            assert messages[1]["role"] == "assistant"
            assert "関連する過去の記憶" in messages[1]["content"]
            assert messages[-1]["role"] == "user"
            assert messages[-1]["content"] == user_message
            
        except ImportError:
            pytest.skip("Context Assembler not implemented yet")

    def test_tc_05_token_estimation_accuracy(self):
        """TC-05: トークン数推定テスト"""
        try:
            from context_assembler.token_estimator import TokenEstimator
            
            estimator = TokenEstimator()
            
            # テストケース
            test_cases = [
                {
                    "messages": [{"role": "user", "content": "こんにちは"}],
                    "expected_range": (10, 30)
                },
                {
                    "messages": [{"role": "user", "content": "Hello World"}],
                    "expected_range": (10, 20)
                },
                {
                    "messages": [
                        {"role": "system", "content": "You are Kana"},
                        {"role": "user", "content": "Resonant Engineは呼吸で動く"},
                        {"role": "assistant", "content": "その通りです"}
                    ],
                    "expected_range": (50, 100)
                }
            ]
            
            for case in test_cases:
                tokens = estimator.estimate(case["messages"])
                min_expected, max_expected = case["expected_range"]
                assert min_expected <= tokens <= max_expected, \
                    f"Expected {min_expected}-{max_expected}, got {tokens}"
                    
        except ImportError:
            pytest.skip("Token Estimator not implemented yet")

    async def test_tc_06_token_compression(self, db_pool):
        """TC-06: トークン圧縮テスト"""
        try:
            from context_assembler.service import ContextAssembler
            from memory_store.models import MemoryResult, MemoryType
            from dashboard.backend.models.message import MessageResponse
            
            context_assembler = ContextAssembler(db_pool)
            
            # 小さいトークン上限を設定
            context_assembler.config.max_tokens = 1000
            
            # 大量のデータ
            memory_layers = {
                "session_summary": "A" * 500,  # 大きなサマリー
                "semantic": [
                    MemoryResult(
                        id=i,
                        content="Memory " * 100,
                        memory_type=MemoryType.LONGTERM,
                        similarity=0.8,
                        created_at=datetime.now(timezone.utc)
                    )
                    for i in range(10)
                ],
                "working": [
                    MessageResponse(
                        id=uuid4(),
                        user_id="test",
                        content="Working " * 50,
                        message_type="user",
                        metadata={},
                        created_at=datetime.now(timezone.utc),
                        updated_at=datetime.now(timezone.utc)
                    )
                    for _ in range(10)
                ]
            }
            
            user_message = "Test query"
            
            # 最初の構築（上限超過）
            messages = context_assembler._build_messages(memory_layers, user_message)
            tokens_before = context_assembler.token_estimator.estimate(messages)
            assert tokens_before > context_assembler._get_token_limit()
            
            # 圧縮
            compressed_messages, tokens_after = context_assembler._compress_context(
                messages, memory_layers, user_message
            )
            
            # 検証
            assert tokens_after <= context_assembler._get_token_limit()
            assert compressed_messages[0]["role"] == "system"
            assert compressed_messages[-1]["role"] == "user"
            assert compressed_messages[-1]["content"] == user_message
            
        except ImportError:
            pytest.skip("Context Assembler not implemented yet")

    async def test_tc_08_full_context_assembly(self, db_pool):
        """TC-08: コンテキスト組み立て統合テスト"""
        try:
            from context_assembler.service import ContextAssembler
            from dashboard.backend.repositories.message_repository import MessageRepository
            from dashboard.backend.models.message import MessageCreate
            from memory_store.service import MemoryStoreService
            from memory_store.repository import MemoryStoreRepository
            from memory_store.models import MemoryType
            
            user_id = f"test_user_{uuid4()}"
            
            # 過去の会話を保存
            message_repo = MessageRepository(db_pool)
            await message_repo.create(MessageCreate(
                user_id=user_id,
                content="Resonant Engineとは？",
                message_type="user",
                metadata={}
            ))
            await message_repo.create(MessageCreate(
                user_id=user_id,
                content="呼吸のリズムで動くAIシステムです",
                message_type="kana",
                metadata={}
            ))
            
            # 長期記憶を保存
            memory_repo = MemoryStoreRepository(db_pool)
            memory_store = MemoryStoreService(memory_repo)
            await memory_store.save_memory(
                "Memory Storeはpgvectorを使う",
                MemoryType.LONGTERM
            )
            
            # コンテキスト組み立て
            context_assembler = ContextAssembler(db_pool)
            assembled = await context_assembler.assemble_context(
                user_message="Memory Storeについて詳しく",
                user_id=user_id
            )
            
            # 検証
            assert len(assembled.messages) >= 3
            assert assembled.messages[0]["role"] == "system"
            assert assembled.messages[-1]["role"] == "user"
            assert assembled.messages[-1]["content"] == "Memory Storeについて詳しく"
            
            # メタデータ検証
            assert assembled.metadata.working_memory_count > 0
            assert assembled.metadata.total_tokens > 0
            assert assembled.metadata.assembly_latency_ms < 100  # 100ms以内
            
        except ImportError:
            pytest.skip("Context Assembler not fully implemented yet")

    @pytest.mark.integration
    async def test_tc_09_kana_bridge_with_context_assembler(self, db_pool):
        """TC-09: KanaAIBridge統合テスト"""
        try:
            from bridge.kana_ai_bridge import KanaAIBridge
            from context_assembler.service import ContextAssembler
            
            # Context Assembler付きでKanaAIBridge初期化
            context_assembler = ContextAssembler(db_pool)
            kana_bridge = KanaAIBridge(context_assembler=context_assembler)
            
            # Intent作成
            intent = {
                "content": "Resonant Engineの記憶システムについて簡潔に説明してください",
                "user_id": f"test_user_{uuid4()}"
            }
            
            # 処理（モック応答を使用）
            with patch.object(kana_bridge, '_call_claude_api') as mock_claude:
                mock_claude.return_value = {
                    "content": [{"text": "Resonant Engineは4層の記憶システムを持っています"}],
                    "usage": {"input_tokens": 100, "output_tokens": 50}
                }
                
                response = await kana_bridge.process_intent(intent)
                
                # 検証
                assert response["status"] == "ok"
                assert "summary" in response
                assert len(response["summary"]) > 0
                
                # Context metadataの検証
                if "context_metadata" in response:
                    assert "working_memory_count" in response["context_metadata"]
                    assert "total_tokens" in response["context_metadata"]
                    
        except ImportError:
            pytest.skip("KanaAIBridge or Context Assembler not implemented yet")

    @pytest.mark.e2e
    async def test_tc_10_claude_remembers_past_conversation(self, db_pool):
        """TC-10: E2E: Claudeが過去の記憶を参照するテスト"""
        try:
            from bridge.kana_ai_bridge import KanaAIBridge
            from context_assembler.service import ContextAssembler
            from dashboard.backend.repositories.message_repository import MessageRepository
            from dashboard.backend.models.message import MessageCreate
            
            user_id = f"test_user_{uuid4()}"
            
            # Context Assembler付きでKanaAIBridge初期化
            context_assembler = ContextAssembler(db_pool)
            kana_bridge = KanaAIBridge(context_assembler=context_assembler)
            message_repo = MessageRepository(db_pool)
            
            # 1回目の会話
            intent1 = {
                "content": "私の名前はHirokiです。Resonant Engineを開発しています。",
                "user_id": user_id
            }
            
            with patch.object(kana_bridge, '_call_claude_api') as mock_claude:
                mock_claude.return_value = {
                    "content": [{"text": "こんにちは、Hirokiさん！Resonant Engineの開発、頑張ってください！"}],
                    "usage": {"input_tokens": 100, "output_tokens": 50}
                }
                
                response1 = await kana_bridge.process_intent(intent1)
                assert response1["status"] == "ok"
            
            # 応答を保存（Working Memoryに追加）
            await message_repo.create(MessageCreate(
                user_id=user_id,
                content=intent1["content"],
                message_type="user",
                metadata={}
            ))
            await message_repo.create(MessageCreate(
                user_id=user_id,
                content=response1["summary"],
                message_type="kana",
                metadata={}
            ))
            
            # 2回目の会話（名前を聞く）
            intent2 = {
                "content": "私の名前を覚えていますか？",
                "user_id": user_id
            }
            
            with patch.object(kana_bridge, '_call_claude_api') as mock_claude:
                # Context Assemblerが過去の会話を含めることを確認
                def check_context(messages, **kwargs):
                    # messagesに過去の会話が含まれているか確認
                    full_context = str(messages)
                    assert "Hiroki" in full_context or "hiroki" in full_context.lower()
                    
                    return {
                        "content": [{"text": "はい、Hirokiさんですね！"}],
                        "usage": {"input_tokens": 150, "output_tokens": 30}
                    }
                
                mock_claude.side_effect = check_context
                
                response2 = await kana_bridge.process_intent(intent2)
                
                # 検証
                assert response2["status"] == "ok"
                if "context_metadata" in response2:
                    assert response2["context_metadata"]["working_memory_count"] > 0
                    
        except ImportError:
            pytest.skip("KanaAIBridge or Context Assembler not implemented yet")

    async def test_tc_12_fallback_without_context_assembler(self):
        """TC-12: E2E: Context Assembler未設定時のfallbackテスト"""
        try:
            from bridge.kana_ai_bridge import KanaAIBridge
            
            # Context Assembler未設定でKanaAIBridge初期化
            bridge = KanaAIBridge()
            
            intent = {
                "content": "Hello, Kana!"
            }
            
            with patch.object(bridge, '_call_claude_api') as mock_claude:
                mock_claude.return_value = {
                    "content": [{"text": "Hello! How can I help you?"}],
                    "usage": {"input_tokens": 50, "output_tokens": 20}
                }
                
                response = await bridge.process_intent(intent)
                
                # 検証
                assert response["status"] == "ok"
                assert "summary" in response
                assert "context_metadata" not in response  # Context Assembler未使用
                
        except ImportError:
            pytest.skip("KanaAIBridge not implemented yet")

    @pytest.mark.performance
    async def test_tc_13_context_assembly_latency(self, db_pool):
        """TC-13: 性能テスト: レイテンシ < 100ms"""
        try:
            from context_assembler.service import ContextAssembler
            import time
            
            context_assembler = ContextAssembler(db_pool)
            user_id = f"perf_user_{uuid4()}"
            
            latencies = []
            
            for i in range(10):
                start = time.time()
                await context_assembler.assemble_context(
                    user_message=f"Test query {i}",
                    user_id=user_id
                )
                latency = (time.time() - start) * 1000
                latencies.append(latency)
            
            # p95計算
            latencies.sort()
            p95 = latencies[int(len(latencies) * 0.95)]
            
            assert p95 < 100, f"p95 latency {p95:.2f}ms exceeds 100ms"
            
        except ImportError:
            pytest.skip("Context Assembler not implemented yet")
