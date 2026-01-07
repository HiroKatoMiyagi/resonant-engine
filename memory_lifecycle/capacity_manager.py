"""
Capacity Manager - 容量管理

メモリの使用状況を監視し、上限に達した際に自動的に低重要度メモリを圧縮します。
"""

import asyncpg
from typing import Dict, Any
import logging

from .compression_service import MemoryCompressionService
from .importance_scorer import ImportanceScorer
from .models import MemoryUsage, CapacityManagementResult

logger = logging.getLogger(__name__)


class CapacityManager:
    """容量管理"""

    # 容量制限
    MEMORY_LIMIT = 10000  # メモリ上限
    AUTO_COMPRESS_THRESHOLD = 0.9  # 90%で自動圧縮
    COMPRESSION_BATCH_SIZE = 1000  # 一度に圧縮する数

    def __init__(
        self,
        pool: asyncpg.Pool,
        compression_service: MemoryCompressionService,
        scorer: ImportanceScorer
    ):
        """
        Args:
            pool: asyncpg connection pool
            compression_service: メモリ圧縮サービス
            scorer: 重要度スコアラー
        """
        self.pool = pool
        self.compression_service = compression_service
        self.scorer = scorer

    async def get_memory_usage(self, user_id: str) -> Dict[str, Any]:
        """
        メモリ使用状況取得

        Args:
            user_id: ユーザーID

        Returns:
            Dict: 使用状況
        """
        try:
            async with self.pool.acquire() as conn:
                # アクティブメモリ数
                active_count = await conn.fetchval("""
                    SELECT COUNT(*) FROM memories WHERE user_id = $1
                """, user_id) or 0

                # アーカイブ数 (table may not exist)
                try:
                    archive_count = await conn.fetchval("""
                        SELECT COUNT(*) FROM memory_archive WHERE user_id = $1
                    """, user_id) or 0
                except Exception:
                    archive_count = 0

                # 合計サイズ（概算）
                total_size = await conn.fetchval("""
                    SELECT SUM(LENGTH(content)) FROM memories WHERE user_id = $1
                """, user_id) or 0

                usage_ratio = active_count / self.MEMORY_LIMIT if self.MEMORY_LIMIT > 0 else 0.0

                return {
                    "active_count": active_count,
                    "archive_count": archive_count,
                    "total_count": active_count + archive_count,
                    "usage_ratio": usage_ratio,
                    "total_size_bytes": total_size,
                    "limit": self.MEMORY_LIMIT
                }
        except Exception as e:
            logger.error(f"Failed to get memory usage: {e}")
            return {
                "active_count": 0,
                "archive_count": 0,
                "total_count": 0,
                "usage_ratio": 0.0,
                "total_size_bytes": 0,
                "limit": self.MEMORY_LIMIT
            }

    async def check_and_manage(self, user_id: str) -> Dict[str, Any]:
        """
        容量チェックと自動管理

        Args:
            user_id: ユーザーID

        Returns:
            Dict: 管理結果
        """
        usage = await self.get_memory_usage(user_id)

        if usage['usage_ratio'] < self.AUTO_COMPRESS_THRESHOLD:
            logger.info(f"Memory usage {usage['usage_ratio']*100:.1f}% - OK")
            return {"action": "none", "usage": usage}

        logger.warning(f"Memory usage {usage['usage_ratio']*100:.1f}% - triggering auto-compress")

        # 1. スコア更新
        updated_count = await self.scorer.update_all_scores(user_id)
        logger.info(f"Updated {updated_count} scores")

        # 2. 低重要度メモリ圧縮
        compress_result = await self.compression_service.compress_low_importance_memories(
            user_id=user_id,
            threshold=0.3,
            limit=self.COMPRESSION_BATCH_SIZE
        )

        # 3. 使用状況再取得
        new_usage = await self.get_memory_usage(user_id)

        return {
            "action": "auto_compress",
            "old_usage": usage,
            "new_usage": new_usage,
            "compress_result": compress_result
        }

    async def cleanup_expired_memories(self) -> int:
        """
        期限切れメモリをクリーンアップ

        Returns:
            int: 削除されたメモリ数
        """
        async with self.pool.acquire() as conn:
            result = await conn.execute("""
                DELETE FROM memories
                WHERE expires_at IS NOT NULL AND expires_at < NOW()
            """)
            # Extract count from result like "DELETE 5"
            deleted_count = int(result.split()[-1]) if result else 0
            logger.info(f"Cleaned up {deleted_count} expired memories")
            return deleted_count
