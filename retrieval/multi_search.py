"""
Multi-Search Executor - 複数検索手法の実装

複数の検索手法を並行実行し、結果を統合します。
「異なる共鳴を同時に鳴らし、調和させる合奏」
"""

import asyncio
from typing import Any, Dict, List, Optional

from memory_store.models import MemoryResult, MemoryType, SourceType
from memory_store.service import MemoryStoreService

from .query_analyzer import QueryIntent, TimeRange
from .strategy import SearchParams, SearchStrategy


class KeywordSearcher:
    """
    キーワード検索（ts_vector）

    PostgreSQLの全文検索機能を使用してキーワードベースの検索を実行します。
    「構造化された言葉の骨格を辿り、ASD認知が安心できる秩序を与える」
    """

    def __init__(self, pool: Any):
        """
        Args:
            pool: asyncpgコネクションプール
        """
        self.pool = pool

    async def search(self, query: str, limit: int = 10) -> List[MemoryResult]:
        """
        キーワード検索

        Args:
            query: 検索クエリ
            limit: 最大返却数

        Returns:
            List[MemoryResult]: 検索結果
        """
        # キーワードをORクエリに変換
        keywords = self._extract_keywords(query)
        if not keywords:
            return []

        tsquery = " | ".join(keywords)

        sql = """
        SELECT
            id, content, memory_type, source_type, metadata, created_at,
            ts_rank(content_tsvector, to_tsquery('simple', $1)) as similarity
        FROM memories
        WHERE content_tsvector @@ to_tsquery('simple', $1)
          AND (expires_at IS NULL OR expires_at > NOW())
          AND is_archived = FALSE
        ORDER BY similarity DESC
        LIMIT $2
        """

        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(sql, tsquery, limit)
                return [self._row_to_memory_result(row) for row in rows]
        except Exception as e:
            print(f"Keyword search error: {e}")
            return []

    def _extract_keywords(self, query: str) -> List[str]:
        """キーワードを抽出"""
        import re

        # 基本的な単語分割
        words = re.findall(r"[a-zA-Z0-9]+|[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]+", query)

        # ストップワード除去と短い単語の除外
        stopwords = {
            "の",
            "は",
            "を",
            "に",
            "が",
            "と",
            "で",
            "や",
            "も",
            "the",
            "a",
            "an",
            "is",
            "are",
            "to",
            "of",
            "in",
            "for",
            "on",
            "with",
        }

        filtered = [w for w in words if w.lower() not in stopwords and len(w) > 1]
        return filtered

    def _row_to_memory_result(self, row: Any) -> MemoryResult:
        """DBの行をMemoryResultに変換"""
        source_type = None
        if row.get("source_type"):
            source_type = SourceType(row["source_type"])

        # スコアをクランプ
        similarity = max(0.0, min(1.0, float(row["similarity"])))

        return MemoryResult(
            id=row["id"],
            content=row["content"],
            memory_type=MemoryType(row["memory_type"]),
            source_type=source_type,
            metadata=row.get("metadata", {}),
            similarity=similarity,
            created_at=row["created_at"],
        )


class TemporalSearcher:
    """
    時系列検索

    時間範囲を考慮した検索を実行します。
    「呼吸の時間軸を守り、『いつ』を問う声に即座に応える時計」
    """

    def __init__(self, pool: Any, embedding_service: Any):
        """
        Args:
            pool: asyncpgコネクションプール
            embedding_service: Embedding生成サービス
        """
        self.pool = pool
        self.embedding_service = embedding_service

    async def search(
        self, query: str, time_range: TimeRange, limit: int = 10
    ) -> List[MemoryResult]:
        """
        時系列検索

        Args:
            query: 検索クエリ
            time_range: 時間範囲
            limit: 最大返却数

        Returns:
            List[MemoryResult]: 検索結果（新しい順）
        """
        # Embedding生成
        embedding = await self.embedding_service.generate_embedding(query)

        sql = """
        SELECT
            id, content, memory_type, source_type, metadata, created_at,
            1 - (embedding <=> $1::vector) as similarity
        FROM memories
        WHERE created_at >= $2
          AND created_at <= $3
          AND (expires_at IS NULL OR expires_at > NOW())
          AND is_archived = FALSE
        ORDER BY created_at DESC, similarity DESC
        LIMIT $4
        """

        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(sql, embedding, time_range.start, time_range.end, limit)
                return [self._row_to_memory_result(row) for row in rows]
        except Exception as e:
            print(f"Temporal search error: {e}")
            return []

    def _row_to_memory_result(self, row: Any) -> MemoryResult:
        """DBの行をMemoryResultに変換"""
        source_type = None
        if row.get("source_type"):
            source_type = SourceType(row["source_type"])

        # スコアをクランプ
        similarity = max(0.0, min(1.0, float(row["similarity"])))

        return MemoryResult(
            id=row["id"],
            content=row["content"],
            memory_type=MemoryType(row["memory_type"]),
            source_type=source_type,
            metadata=row.get("metadata", {}),
            similarity=similarity,
            created_at=row["created_at"],
        )


class MultiSearchExecutor:
    """
    複数検索の並行実行

    複数の検索手法を並行して実行し、結果を統合します。
    """

    def __init__(
        self,
        memory_store: MemoryStoreService,
        keyword_searcher: Optional[KeywordSearcher] = None,
        temporal_searcher: Optional[TemporalSearcher] = None,
    ):
        """
        Args:
            memory_store: Memory Store サービス
            keyword_searcher: キーワード検索サービス（オプション）
            temporal_searcher: 時系列検索サービス（オプション）
        """
        self.memory_store = memory_store
        self.keyword_searcher = keyword_searcher
        self.temporal_searcher = temporal_searcher

    async def execute(
        self, query: str, strategy: SearchStrategy, params: SearchParams, intent: QueryIntent
    ) -> Dict[str, List[MemoryResult]]:
        """
        戦略に応じて複数検索を並行実行

        Args:
            query: 検索クエリ
            strategy: 検索戦略
            params: 検索パラメータ
            intent: クエリ意図

        Returns:
            Dict[str, List[MemoryResult]]: {検索手法: 結果リスト}
        """
        tasks: Dict[str, Any] = {}

        # ベクトル検索
        if strategy in [
            SearchStrategy.SEMANTIC_ONLY,
            SearchStrategy.KEYWORD_BOOST,
            SearchStrategy.HYBRID,
        ]:
            tasks["vector"] = self.memory_store.search_similar(
                query=query, limit=params.limit, similarity_threshold=params.similarity_threshold
            )

        # キーワード検索
        if strategy in [SearchStrategy.KEYWORD_BOOST, SearchStrategy.HYBRID]:
            if self.keyword_searcher:
                tasks["keyword"] = self.keyword_searcher.search(query=query, limit=params.limit)

        # 時系列検索
        if strategy == SearchStrategy.TEMPORAL and intent.time_range:
            if self.temporal_searcher:
                tasks["temporal"] = self.temporal_searcher.search(
                    query=query, time_range=intent.time_range, limit=params.limit
                )
            else:
                # Temporal Searcherがない場合はベクトル検索のみ
                tasks["vector"] = self.memory_store.search_similar(
                    query=query,
                    limit=params.limit,
                    similarity_threshold=params.similarity_threshold,
                )

        if not tasks:
            return {}

        # 並行実行
        task_names = list(tasks.keys())
        task_coroutines = list(tasks.values())

        try:
            results = await asyncio.gather(*task_coroutines, return_exceptions=True)

            # 結果を辞書にマッピング
            output: Dict[str, List[MemoryResult]] = {}
            for name, result in zip(task_names, results):
                if isinstance(result, Exception):
                    print(f"Search method {name} failed: {result}")
                    output[name] = []
                else:
                    output[name] = result

            return output
        except Exception as e:
            print(f"Multi-search execution error: {e}")
            return {}
