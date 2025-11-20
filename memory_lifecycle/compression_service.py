"""
Memory Compression Service - メモリ圧縮サービス

Claude Haikuを使ってメモリを要約し、アーカイブに保存します。
"""

import asyncpg
from typing import Dict, Any
import anthropic
import logging
import json

from .models import MemoryArchive, LifecycleEvent, CompressionResult, BatchCompressionResult

logger = logging.getLogger(__name__)


class MemoryCompressionService:
    """メモリ圧縮サービス"""

    def __init__(self, pool: asyncpg.Pool, anthropic_api_key: str):
        """
        Args:
            pool: asyncpg connection pool
            anthropic_api_key: Anthropic API key for Claude Haiku
        """
        self.pool = pool
        self.claude = anthropic.Anthropic(api_key=anthropic_api_key)

    async def summarize_content(self, content: str) -> str:
        """
        Claude Haikuで内容を要約

        Args:
            content: 元コンテンツ

        Returns:
            str: 要約文
        """
        try:
            message = self.claude.messages.create(
                model="claude-haiku-3-5-20241022",
                max_tokens=200,
                messages=[{
                    "role": "user",
                    "content": f"""以下の会話内容を1-2文で簡潔に要約してください。
重要な情報（日付、名前、数値など）は必ず残してください。

内容:
{content}

要約:"""
                }]
            )

            summary = message.content[0].text.strip()
            logger.debug(f"Summarized: {len(content)} chars → {len(summary)} chars")
            return summary

        except Exception as e:
            logger.error(f"Claude Haiku summarization failed: {e}")
            # Fallback: 単純な切り詰め
            return content[:100] + "..." if len(content) > 100 else content

    async def compress_memory(
        self,
        memory_id: str,
        reason: str = "low_importance"
    ) -> Dict[str, Any]:
        """
        単一メモリの圧縮

        Args:
            memory_id: メモリID
            reason: 圧縮理由

        Returns:
            Dict: 圧縮結果
        """
        async with self.pool.acquire() as conn:
            # メモリ取得
            memory = await conn.fetchrow("""
                SELECT * FROM semantic_memories WHERE id = $1
            """, memory_id)

            if not memory:
                raise ValueError(f"Memory not found: {memory_id}")

            # 要約生成
            summary = await self.summarize_content(memory['content'])

            # サイズ計算
            original_size = len(memory['content'].encode('utf-8'))
            compressed_size = len(summary.encode('utf-8'))
            compression_ratio = (original_size - compressed_size) / original_size if original_size > 0 else 0

            # Archive保存（sprint8の教訓を活かし、JSONB型は使用しない）
            archive_id = await conn.fetchval("""
                INSERT INTO memory_archive
                    (user_id, original_memory_id, original_content, original_embedding,
                     compressed_summary, compression_method, compressed_at,
                     original_size_bytes, compressed_size_bytes, compression_ratio,
                     final_importance_score, archive_reason)
                VALUES ($1, $2, $3, $4, $5, 'claude_haiku', NOW(), $6, $7, $8, $9, $10)
                RETURNING id
            """, memory['user_id'], memory['id'], memory['content'],
                memory['embedding'], summary, original_size, compressed_size,
                compression_ratio, memory['importance_score'], reason)

            # 元メモリ削除
            await conn.execute("DELETE FROM semantic_memories WHERE id = $1", memory_id)

            # ログ記録（event_detailsはJSONB型なので、json.dumps()で文字列化し::jsonbでキャスト）
            event_details = json.dumps({
                "archive_id": str(archive_id),
                "compression_ratio": compression_ratio,
                "reason": reason
            })
            await conn.execute("""
                INSERT INTO memory_lifecycle_log
                    (user_id, memory_id, event_type, event_details, score_before)
                VALUES ($1, $2, 'compress', $3::jsonb, $4)
            """, memory['user_id'], memory['id'], event_details, memory['importance_score'])

            logger.info(f"Compressed memory {memory_id}: {compression_ratio*100:.1f}% reduction")

            return {
                "archive_id": str(archive_id),
                "original_size": original_size,
                "compressed_size": compressed_size,
                "compression_ratio": compression_ratio
            }

    async def compress_low_importance_memories(
        self,
        user_id: str,
        threshold: float = 0.3,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        低重要度メモリの一括圧縮

        Args:
            user_id: ユーザーID
            threshold: 重要度閾値（これ以下を圧縮）
            limit: 一度に圧縮する最大数

        Returns:
            Dict: 圧縮結果サマリ
        """
        async with self.pool.acquire() as conn:
            # 低重要度メモリ取得
            memories = await conn.fetch("""
                SELECT id, importance_score FROM semantic_memories
                WHERE user_id = $1 AND importance_score < $2
                ORDER BY importance_score ASC
                LIMIT $3
            """, user_id, threshold, limit)

            compressed_count = 0
            failed_count = 0
            total_original_size = 0
            total_compressed_size = 0

            for memory in memories:
                try:
                    result = await self.compress_memory(
                        str(memory['id']),
                        reason="low_importance"
                    )
                    compressed_count += 1
                    total_original_size += result['original_size']
                    total_compressed_size += result['compressed_size']
                except Exception as e:
                    logger.error(f"Compression failed for {memory['id']}: {e}")
                    failed_count += 1

            overall_ratio = (total_original_size - total_compressed_size) / total_original_size if total_original_size > 0 else 0

            logger.info(f"Batch compression: {compressed_count} succeeded, {failed_count} failed, {overall_ratio*100:.1f}% reduction")

            return {
                "compressed_count": compressed_count,
                "failed_count": failed_count,
                "overall_compression_ratio": overall_ratio,
                "total_original_size": total_original_size,
                "total_compressed_size": total_compressed_size
            }

    async def restore_from_archive(self, archive_id: str) -> str:
        """
        アーカイブからメモリを復元

        Args:
            archive_id: アーカイブID

        Returns:
            str: 復元されたメモリID
        """
        async with self.pool.acquire() as conn:
            # アーカイブ取得
            archive = await conn.fetchrow("""
                SELECT * FROM memory_archive WHERE id = $1
            """, archive_id)

            if not archive:
                raise ValueError(f"Archive not found: {archive_id}")

            # メモリ復元
            memory_id = await conn.fetchval("""
                INSERT INTO semantic_memories
                    (user_id, content, embedding, importance_score, created_at)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
            """, archive['user_id'], archive['original_content'],
                archive['original_embedding'], archive['final_importance_score'],
                archive['compressed_at'])

            # アーカイブ削除
            await conn.execute("DELETE FROM memory_archive WHERE id = $1", archive_id)

            logger.info(f"Restored memory {memory_id} from archive {archive_id}")

            return str(memory_id)
