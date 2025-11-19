"""
User Profile Integration Tests

Sprint 8: User Profile & Persistent Context
統合テスト（CLAUDE.md → DB → Context Assembly）
"""

import pytest
import asyncpg
import os
from user_profile.sync import ClaudeMdSync
from user_profile.repository import UserProfileRepository
from user_profile.context_provider import ProfileContextProvider


@pytest.fixture
async def db_pool():
    """テスト用データベース接続プール"""
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://resonant:password@localhost:5432/resonant"
    )

    pool = await asyncpg.create_pool(database_url)
    yield pool
    await pool.close()


@pytest.mark.asyncio
async def test_claude_md_sync_integration(db_pool):
    """CLAUDE.md同期統合テスト"""
    sync_service = ClaudeMdSync(db_pool, "/home/user/resonant-engine/CLAUDE.md")

    # 同期実行
    result = await sync_service.sync()

    # 結果検証
    assert result["status"] == "ok"
    assert result["counts"]["cognitive_traits"] >= 4
    assert result["counts"]["family_members"] >= 5
    assert result["counts"]["goals"] >= 3
    assert result["counts"]["resonant_concepts"] >= 3


@pytest.mark.asyncio
async def test_profile_context_generation(db_pool):
    """プロフィールコンテキスト生成テスト"""
    # CLAUDE.md同期
    sync_service = ClaudeMdSync(db_pool, "/home/user/resonant-engine/CLAUDE.md")
    await sync_service.sync()

    # Profile Context Provider作成
    repo = UserProfileRepository(db_pool)
    provider = ProfileContextProvider(repo)

    # コンテキスト取得
    context = await provider.get_profile_context("hiroki")

    # 検証
    assert context is not None
    assert context.system_prompt_adjustment != ""
    assert context.context_section != ""
    assert len(context.response_guidelines) > 0
    assert context.token_count > 0
    assert context.token_count < 600  # トークン上限


@pytest.mark.asyncio
async def test_system_prompt_adjustment(db_pool):
    """System Prompt調整生成テスト"""
    # CLAUDE.md同期
    sync_service = ClaudeMdSync(db_pool, "/home/user/resonant-engine/CLAUDE.md")
    await sync_service.sync()

    # Profile Context Provider作成
    repo = UserProfileRepository(db_pool)
    provider = ProfileContextProvider(repo)

    # コンテキスト取得
    context = await provider.get_profile_context("hiroki")

    # System Prompt調整検証
    adjustment = context.system_prompt_adjustment

    assert "ASD" in adjustment or "認知特性" in adjustment
    assert "選択肢" in adjustment
    assert "否定" in adjustment or "肯定的" in adjustment
    assert "構造" in adjustment or "階層" in adjustment


@pytest.mark.asyncio
async def test_profile_caching(db_pool):
    """キャッシング機能テスト"""
    import time

    # CLAUDE.md同期
    sync_service = ClaudeMdSync(db_pool, "/home/user/resonant-engine/CLAUDE.md")
    await sync_service.sync()

    # Profile Context Provider作成
    repo = UserProfileRepository(db_pool)
    provider = ProfileContextProvider(repo)

    # 1回目: DB取得
    start_time = time.time()
    context1 = await provider.get_profile_context("hiroki")
    first_duration = time.time() - start_time

    # 2回目: キャッシュヒット
    start_time = time.time()
    context2 = await provider.get_profile_context("hiroki")
    second_duration = time.time() - start_time

    # 検証
    assert context1 is not None
    assert context2 is not None
    assert context1.token_count == context2.token_count

    # キャッシュヒット時は高速
    assert second_duration < first_duration / 2
