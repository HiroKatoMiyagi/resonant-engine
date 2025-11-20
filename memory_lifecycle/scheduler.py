"""
Lifecycle Scheduler - ライフサイクルスケジューラー

日次メンテナンスや定期的なクリーンアップを実行します。
"""

import asyncpg
from typing import List
import logging
from datetime import datetime, timedelta

from .importance_scorer import ImportanceScorer
from .capacity_manager import CapacityManager
from .compression_service import MemoryCompressionService

logger = logging.getLogger(__name__)


class LifecycleScheduler:
    """ライフサイクルスケジューラー"""

    def __init__(
        self,
        pool: asyncpg.Pool,
        scorer: ImportanceScorer,
        capacity_manager: CapacityManager
    ):
        """
        Args:
            pool: asyncpg connection pool
            scorer: 重要度スコアラー
            capacity_manager: 容量管理マネージャー
        """
        self.pool = pool
        self.scorer = scorer
        self.capacity_manager = capacity_manager

    async def get_all_users(self) -> List[str]:
        """全ユーザーID取得"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT DISTINCT user_id FROM semantic_memories
            """)
            return [row['user_id'] for row in rows]

    async def daily_maintenance(self):
        """日次メンテナンス"""
        logger.info("=== Daily Lifecycle Maintenance Started ===")

        users = await self.get_all_users()
        logger.info(f"Processing {len(users)} users")

        for user_id in users:
            try:
                # 1. スコア更新
                updated = await self.scorer.update_all_scores(user_id)
                logger.info(f"User {user_id}: updated {updated} scores")

                # 2. 容量チェック＆管理
                result = await self.capacity_manager.check_and_manage(user_id)
                logger.info(f"User {user_id}: {result['action']}")

            except Exception as e:
                logger.error(f"Maintenance failed for user {user_id}: {e}")

        logger.info("=== Daily Lifecycle Maintenance Completed ===")

    async def cleanup_expired_archives(self, retention_days: int = 90):
        """期限切れアーカイブのクリーンアップ"""
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)

        async with self.pool.acquire() as conn:
            result = await conn.execute("""
                DELETE FROM memory_archive
                WHERE retention_until IS NOT NULL
                  AND retention_until < $1
            """, cutoff_date)

            # asyncpgのexecute()の戻り値は "DELETE N" という文字列
            # そこから削除件数を抽出
            deleted_count = 0
            if result:
                try:
                    deleted_count = int(result.split()[-1])
                except (ValueError, IndexError):
                    deleted_count = 0

            logger.info(f"Deleted {deleted_count} expired archives")
