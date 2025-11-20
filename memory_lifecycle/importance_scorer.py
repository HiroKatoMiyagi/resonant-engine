"""
Importance Scorer - メモリ重要度スコアリング

時間減衰とアクセス強化に基づいて、メモリの重要度スコアを計算・更新します。
"""

import asyncpg
from datetime import datetime
from typing import Optional
import logging

from .models import MemoryScore, LifecycleEvent

logger = logging.getLogger(__name__)


class ImportanceScorer:
    """メモリ重要度スコアリング"""

    # パラメータ
    DECAY_RATE = 0.95  # 週ごとに5%減衰
    BOOST_PER_ACCESS = 0.1  # アクセスごとに+10%
    MAX_SCORE = 1.0
    MIN_SCORE = 0.0

    def __init__(self, pool: asyncpg.Pool):
        """
        Args:
            pool: asyncpg connection pool
        """
        self.pool = pool

    def calculate_time_decay(self, created_at: datetime) -> float:
        """
        時間減衰係数計算

        Args:
            created_at: 作成日時

        Returns:
            float: 減衰係数（0.0 - 1.0）
        """
        weeks_elapsed = (datetime.utcnow() - created_at).days / 7.0
        decay_factor = self.DECAY_RATE ** weeks_elapsed
        return decay_factor

    def calculate_access_boost(self, access_count: int) -> float:
        """
        アクセス強化係数計算

        Args:
            access_count: アクセス回数

        Returns:
            float: 強化係数（>= 1.0）
        """
        boost_factor = 1.0 + (access_count * self.BOOST_PER_ACCESS)
        return boost_factor

    def calculate_score(
        self,
        base_score: float,
        created_at: datetime,
        access_count: int
    ) -> float:
        """
        重要度スコア計算

        Args:
            base_score: 基本スコア
            created_at: 作成日時
            access_count: アクセス回数

        Returns:
            float: 重要度スコア（0.0 - 1.0）
        """
        time_decay = self.calculate_time_decay(created_at)
        access_boost = self.calculate_access_boost(access_count)

        score = base_score * time_decay * access_boost

        # 0-1の範囲にクリップ
        return max(self.MIN_SCORE, min(self.MAX_SCORE, score))

    async def update_memory_score(self, memory_id: str) -> float:
        """
        単一メモリのスコア更新

        Args:
            memory_id: メモリID

        Returns:
            float: 新しいスコア
        """
        async with self.pool.acquire() as conn:
            # メモリ情報取得
            memory = await conn.fetchrow("""
                SELECT id, user_id, created_at, importance_score, access_count
                FROM semantic_memories
                WHERE id = $1
            """, memory_id)

            if not memory:
                raise ValueError(f"Memory not found: {memory_id}")

            # 新スコア計算
            old_score = memory['importance_score']
            new_score = self.calculate_score(
                base_score=0.5,  # 基本スコアは固定
                created_at=memory['created_at'],
                access_count=memory['access_count']
            )

            # スコア更新
            await conn.execute("""
                UPDATE semantic_memories
                SET importance_score = $1,
                    decay_applied_at = NOW()
                WHERE id = $2
            """, new_score, memory_id)

            # ログ記録
            await conn.execute("""
                INSERT INTO memory_lifecycle_log
                    (user_id, memory_id, event_type, score_before, score_after, event_at)
                VALUES ($1, $2, 'score_update', $3, $4, NOW())
            """, memory['user_id'], memory_id, old_score, new_score)

            logger.debug(f"Memory {memory_id}: score {old_score:.3f} → {new_score:.3f}")

            return new_score

    async def update_all_scores(self, user_id: str) -> int:
        """
        全メモリのスコアを一括更新

        Args:
            user_id: ユーザーID

        Returns:
            int: 更新したメモリ数
        """
        async with self.pool.acquire() as conn:
            memories = await conn.fetch("""
                SELECT id FROM semantic_memories
                WHERE user_id = $1
            """, user_id)

            updated_count = 0
            for memory in memories:
                try:
                    await self.update_memory_score(str(memory['id']))
                    updated_count += 1
                except Exception as e:
                    logger.error(f"Failed to update score for {memory['id']}: {e}")

            logger.info(f"Updated {updated_count} memory scores for user {user_id}")
            return updated_count

    async def boost_on_access(self, memory_id: str):
        """
        アクセス時のスコア強化

        Args:
            memory_id: メモリID
        """
        async with self.pool.acquire() as conn:
            # アクセスカウント更新
            await conn.execute("""
                UPDATE semantic_memories
                SET access_count = access_count + 1,
                    last_accessed_at = NOW()
                WHERE id = $1
            """, memory_id)

            # スコア再計算
            await self.update_memory_score(memory_id)
