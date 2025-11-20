"""
Memory Lifecycle E2E Integration Tests
"""

import pytest
import os
from datetime import datetime, timedelta

# Note: これらのテストは実際のPostgreSQLとAnthropicAPIキーが必要です
# 開発環境で実行する際は、以下の環境変数を設定してください：
# - DATABASE_URL
# - ANTHROPIC_API_KEY


@pytest.mark.skipif(
    not os.getenv("DATABASE_URL") or not os.getenv("ANTHROPIC_API_KEY"),
    reason="DATABASE_URL or ANTHROPIC_API_KEY not set"
)
@pytest.mark.asyncio
async def test_importance_scorer_integration(db_pool):
    """Importance Scorer統合テスト"""
    from memory_lifecycle.importance_scorer import ImportanceScorer

    scorer = ImportanceScorer(db_pool)
    user_id = "test_user"

    # テストメモリ作成
    async with db_pool.acquire() as conn:
        memory_id = await conn.fetchval("""
            INSERT INTO semantic_memories
                (user_id, content, importance_score, created_at, access_count)
            VALUES ($1, 'テスト', 0.5, NOW() - INTERVAL '7 days', 0)
            RETURNING id
        """, user_id)

    # スコア更新
    new_score = await scorer.update_memory_score(str(memory_id))

    # 検証: 1週間減衰後
    assert 0.47 < new_score < 0.48

    # DB確認
    async with db_pool.acquire() as conn:
        memory = await conn.fetchrow("""
            SELECT importance_score FROM semantic_memories WHERE id = $1
        """, memory_id)

        assert 0.47 < memory['importance_score'] < 0.48

    # クリーンアップ
    async with db_pool.acquire() as conn:
        await conn.execute("DELETE FROM semantic_memories WHERE user_id = $1", user_id)


@pytest.mark.skipif(
    not os.getenv("DATABASE_URL") or not os.getenv("ANTHROPIC_API_KEY"),
    reason="DATABASE_URL or ANTHROPIC_API_KEY not set"
)
@pytest.mark.asyncio
async def test_compression_service_integration(db_pool):
    """Compression Service統合テスト"""
    from memory_lifecycle.compression_service import MemoryCompressionService

    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    service = MemoryCompressionService(db_pool, anthropic_api_key)
    user_id = "test_user"

    # テストメモリ作成
    long_content = "これは非常に長い会話のテストです。" * 20
    async with db_pool.acquire() as conn:
        memory_id = await conn.fetchval("""
            INSERT INTO semantic_memories (user_id, content, importance_score)
            VALUES ($1, $2, 0.2)
            RETURNING id
        """, user_id, long_content)

    # 圧縮実行
    result = await service.compress_memory(str(memory_id))

    # 検証
    assert result['compression_ratio'] > 0.5  # 50%以上圧縮
    assert result['original_size'] > result['compressed_size']

    # 元メモリ削除確認
    async with db_pool.acquire() as conn:
        memory = await conn.fetchrow("""
            SELECT * FROM semantic_memories WHERE id = $1
        """, memory_id)
        assert memory is None

    # アーカイブ確認
    async with db_pool.acquire() as conn:
        archive = await conn.fetchrow("""
            SELECT * FROM memory_archive WHERE id = $1
        """, result['archive_id'])

        assert archive is not None
        assert archive['compression_method'] == 'claude_haiku'

    # クリーンアップ
    async with db_pool.acquire() as conn:
        await conn.execute("DELETE FROM memory_archive WHERE user_id = $1", user_id)


@pytest.mark.skipif(
    not os.getenv("DATABASE_URL"),
    reason="DATABASE_URL not set"
)
@pytest.mark.asyncio
async def test_capacity_manager_integration(db_pool):
    """Capacity Manager統合テスト"""
    from memory_lifecycle.importance_scorer import ImportanceScorer
    from memory_lifecycle.compression_service import MemoryCompressionService
    from memory_lifecycle.capacity_manager import CapacityManager

    scorer = ImportanceScorer(db_pool)
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "dummy_key")
    compression_service = MemoryCompressionService(db_pool, anthropic_api_key)
    capacity_manager = CapacityManager(db_pool, compression_service, scorer)

    # テスト用に上限を変更
    capacity_manager.MEMORY_LIMIT = 100
    capacity_manager.AUTO_COMPRESS_THRESHOLD = 0.9

    user_id = "test_user"

    # メモリ100件作成
    async with db_pool.acquire() as conn:
        for i in range(100):
            await conn.execute("""
                INSERT INTO semantic_memories (user_id, content, importance_score)
                VALUES ($1, $2, 0.5)
            """, user_id, f"テスト {i}")

    # 使用状況取得
    usage = await capacity_manager.get_memory_usage(user_id)

    # 検証
    assert usage['active_count'] == 100
    assert usage['usage_ratio'] == 100 / 100  # 100%
    assert usage['limit'] == 100

    # クリーンアップ
    async with db_pool.acquire() as conn:
        await conn.execute("DELETE FROM semantic_memories WHERE user_id = $1", user_id)


@pytest.mark.skipif(
    not os.getenv("DATABASE_URL"),
    reason="DATABASE_URL not set"
)
@pytest.mark.asyncio
async def test_full_lifecycle_flow(db_pool):
    """完全ライフサイクルフローテスト"""
    from memory_lifecycle.importance_scorer import ImportanceScorer
    from memory_lifecycle.compression_service import MemoryCompressionService

    scorer = ImportanceScorer(db_pool)
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "dummy_key")
    compression_service = MemoryCompressionService(db_pool, anthropic_api_key)
    user_id = "test_user"

    # 1. メモリ作成（30日前）
    async with db_pool.acquire() as conn:
        memory_id = await conn.fetchval("""
            INSERT INTO semantic_memories
                (user_id, content, importance_score, created_at, access_count)
            VALUES ($1, $2, 0.5, NOW() - INTERVAL '30 days', 0)
            RETURNING id
        """, user_id, "古い会話のテスト " * 30)

    # 2. スコア減衰適用
    new_score = await scorer.update_memory_score(str(memory_id))
    assert new_score < 0.5  # 減衰確認

    # 3. 低重要度判定（< 0.3）なら圧縮
    if new_score < 0.3:
        if os.getenv("ANTHROPIC_API_KEY"):  # APIキーがある場合のみ実行
            result = await compression_service.compress_memory(str(memory_id))
            assert result['compression_ratio'] > 0.5

            # アーカイブ確認
            async with db_pool.acquire() as conn:
                archive = await conn.fetchrow("""
                    SELECT * FROM memory_archive WHERE id = $1
                """, result['archive_id'])
                assert archive is not None

            # クリーンアップ
            async with db_pool.acquire() as conn:
                await conn.execute("DELETE FROM memory_archive WHERE user_id = $1", user_id)
    else:
        # スコアが0.3以上の場合はクリーンアップ
        async with db_pool.acquire() as conn:
            await conn.execute("DELETE FROM semantic_memories WHERE user_id = $1", user_id)
