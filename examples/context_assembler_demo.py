#!/usr/bin/env python3
"""
Context Assembler 実運用デモ

このスクリプトは、実際の運用環境でContext Assemblerがどのように動作するかを示します。

前提条件:
- PostgreSQLが起動している
- messagesテーブルに過去の会話がある
- memoriesテーブルに長期記憶がある
- ANTHROPIC_API_KEYが設定されている
"""

import asyncio
import os
from datetime import datetime

# Context Assembler
from context_assembler import ContextAssemblerService, get_default_config

# Dependencies
from backend.app.repositories.message_repo import MessageRepository
from bridge.memory.repositories import SessionRepository
from retrieval.orchestrator import create_orchestrator
from memory_store.service import MemoryStoreService
from memory_store.repository import MemoryRepository
from memory_store.embedding import EmbeddingService

# KanaAIBridge
from bridge.providers.ai.kana_ai_bridge import KanaAIBridge

# Database
import asyncpg


async def main():
    print("=== Context Assembler 実運用デモ ===\n")

    # 1. データベース接続
    print("1. データベース接続中...")
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/resonant")
    pool = await asyncpg.create_pool(db_url)
    print(f"   ✓ 接続完了: {db_url}\n")

    # 2. 依存コンポーネント初期化
    print("2. コンポーネント初期化中...")

    # Message Repository
    message_repo = MessageRepository()

    # Session Repository
    session_repo = SessionRepository()

    # Memory Store & Retrieval Orchestrator
    memory_repo = MemoryRepository(pool)
    embedding_service = EmbeddingService()
    memory_store = MemoryStoreService(memory_repo, embedding_service)
    retrieval = create_orchestrator(memory_store, pool, embedding_service)

    print("   ✓ 初期化完了\n")

    # 3. Context Assembler初期化
    print("3. Context Assembler初期化中...")
    config = get_default_config()
    context_assembler = ContextAssemblerService(
        retrieval_orchestrator=retrieval,
        message_repository=message_repo,
        session_repository=session_repo,
        config=config,
    )
    print("   ✓ Context Assembler準備完了\n")

    # 4. KanaAIBridge初期化（Context Assembler付き）
    print("4. KanaAIBridge初期化中...")
    bridge = KanaAIBridge(context_assembler=context_assembler)
    print("   ✓ KanaAIBridge準備完了\n")

    # === 実運用シミュレーション ===

    print("=" * 60)
    print("実運用シミュレーション: ユーザーが質問")
    print("=" * 60)

    user_id = "hiroki"
    user_message = "私の名前を覚えていますか？"

    print(f"\nユーザー: {user_message}")
    print("\n--- Context Assembler 内部動作 ---")

    # 5. Context組み立て（デバッグ出力付き）
    print("\n[Phase 1] Working Memory取得中...")
    working_messages, total = await message_repo.list(user_id=user_id, limit=10)
    print(f"   → PostgreSQLから直近10件取得（全{total}件中）")
    for i, msg in enumerate(reversed(working_messages[-3:]), 1):
        print(f"      {i}. [{msg.message_type}] {msg.content[:50]}...")

    print("\n[Phase 2] Semantic Memory検索中...")
    from retrieval.orchestrator import RetrievalOptions
    retrieval_response = await retrieval.retrieve(
        query=user_message,
        options=RetrievalOptions(limit=5, log_metrics=False)
    )
    print(f"   → ベクトル検索で関連性の高い5件取得")
    for i, mem in enumerate(retrieval_response.results[:3], 1):
        print(f"      {i}. {mem.content[:50]}... (類似度: {mem.similarity:.2f})")

    print("\n[Phase 3] メッセージリスト構築中...")
    assembled = await context_assembler.assemble_context(
        user_message=user_message,
        user_id=user_id,
    )
    print(f"   → {len(assembled.messages)}件のメッセージを構築")
    print(f"   → トークン数: {assembled.metadata.total_tokens}")
    print(f"   → 組み立て時間: {assembled.metadata.assembly_latency_ms:.2f}ms")

    print("\n[Phase 4] Claude API呼び出し中...")

    # 6. Claude API呼び出し
    intent = {
        "content": user_message,
        "user_id": user_id,
    }

    response = await bridge.process_intent(intent)

    print("\n--- Claude API レスポンス ---")
    print(f"Status: {response['status']}")

    if response['status'] == 'ok':
        print(f"\nClaude: {response['summary']}\n")

        if 'context_metadata' in response:
            print("Context Metadata:")
            print(f"  - Working Memory使用: {response['context_metadata']['working_memory_count']}件")
            print(f"  - Semantic Memory使用: {response['context_metadata']['semantic_memory_count']}件")
            print(f"  - 総トークン数: {response['context_metadata']['total_tokens']}")
            print(f"  - 圧縮適用: {response['context_metadata']['compression_applied']}")
    else:
        print(f"Error: {response.get('reason', 'Unknown error')}")

    print("\n" + "=" * 60)
    print("データ選別の効果")
    print("=" * 60)
    print(f"PostgreSQL蓄積データ: {total}件のメッセージ + 1000+件の記憶")
    print(f"Claude APIに送信: {len(assembled.messages)}件のメッセージ")
    print(f"削減率: {(1 - len(assembled.messages) / (total + 1000)) * 100:.1f}%")
    print("\n→ 大量のデータから「関連するもの」だけを選別して送信！")

    # 7. クリーンアップ
    await pool.close()
    print("\n✓ デモ完了")


if __name__ == "__main__":
    asyncio.run(main())
