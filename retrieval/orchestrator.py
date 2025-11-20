"""
Retrieval Orchestrator - 検索オーケストレーター

全コンポーネントを統合し、記憶検索のエントリーポイントを提供します。
「質問という吸気に対する想起の戦略を決める知性」
"""

import time
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from memory_store.models import MemoryResult
from memory_store.service import MemoryStoreService

from .metrics import MetricsCollector, SearchMetrics
from .multi_search import KeywordSearcher, MultiSearchExecutor, TemporalSearcher
from .query_analyzer import QueryAnalyzer, QueryIntent
from .reranker import Reranker
from .strategy import SearchParams, SearchStrategy, StrategySelector


class RetrievalOptions(BaseModel):
    """検索オプション"""

    force_strategy: Optional[SearchStrategy] = None
    limit: Optional[int] = Field(default=None, ge=1, le=1000)
    include_metadata_details: bool = False
    log_metrics: bool = True

    class Config:
        use_enum_values = False


class RetrievalMetadata(BaseModel):
    """検索メタデータ"""

    strategy_used: SearchStrategy
    query_intent: QueryIntent
    total_latency_ms: float = Field(..., ge=0)
    search_breakdown: Dict[str, float] = Field(default_factory=dict)
    num_results_before_rerank: int = Field(..., ge=0)
    num_results_after_rerank: int = Field(..., ge=0)

    class Config:
        use_enum_values = False


class RetrievalResponse(BaseModel):
    """検索レスポンス"""

    results: List[MemoryResult]
    metadata: RetrievalMetadata

    class Config:
        use_enum_values = False
        from_attributes = True


class RetrievalOrchestrator:
    """
    検索オーケストレーター

    クエリ分析、戦略選択、複数検索実行、リランキング、メトリクス収集を
    統合し、最適な記憶検索を提供します。
    """

    def __init__(
        self,
        query_analyzer: QueryAnalyzer,
        strategy_selector: StrategySelector,
        multi_search_executor: MultiSearchExecutor,
        reranker: Reranker,
        metrics_collector: MetricsCollector,
        scorer: Optional["ImportanceScorer"] = None,  # Sprint 9: Memory Lifecycle
    ):
        """
        Args:
            query_analyzer: クエリ分析サービス
            strategy_selector: 戦略選択サービス
            multi_search_executor: 複数検索実行サービス
            reranker: リランキングサービス
            metrics_collector: メトリクス収集サービス
            scorer: 重要度スコアラー (Sprint 9)
        """
        self.query_analyzer = query_analyzer
        self.strategy_selector = strategy_selector
        self.multi_search_executor = multi_search_executor
        self.reranker = reranker
        self.metrics_collector = metrics_collector
        self.scorer = scorer  # Sprint 9: Memory Lifecycle

    async def retrieve(
        self, query: str, options: Optional[RetrievalOptions] = None
    ) -> RetrievalResponse:
        """
        記憶検索のエントリーポイント

        Args:
            query: 検索クエリ
            options: 検索オプション

        Returns:
            RetrievalResponse: 検索結果 + メタデータ
        """
        start_time = time.time()
        options = options or RetrievalOptions()

        # 1. Query Analyzer
        intent = self.query_analyzer.analyze(query)

        # 2. Strategy Selector
        strategy_start = time.time()
        if options.force_strategy:
            strategy = options.force_strategy
        else:
            strategy = self.strategy_selector.select_strategy(intent)

        params = self.strategy_selector.optimize_params(intent, strategy)
        if options.limit:
            params.limit = options.limit

        strategy_selection_time = (time.time() - strategy_start) * 1000

        # 3. Multi-Search Executor
        search_start = time.time()
        search_results = await self.multi_search_executor.execute(
            query=query, strategy=strategy, params=params, intent=intent
        )
        search_time = time.time() - search_start

        # 各検索手法のレイテンシを計算（簡易版：全体時間を均等に分割）
        search_latencies = {}
        if search_results:
            per_method_time = (search_time * 1000) / len(search_results)
            for method in search_results.keys():
                search_latencies[method] = per_method_time

        num_before_rerank = sum(len(r) for r in search_results.values())

        # 4. Reranker
        rerank_start = time.time()
        final_results = self.reranker.rerank(search_results, params)
        rerank_latency = (time.time() - rerank_start) * 1000

        total_latency = (time.time() - start_time) * 1000

        # 5. Metrics Collector
        metrics = await self.metrics_collector.collect(
            query=query,
            strategy=strategy,
            results=final_results,
            latencies=search_latencies,
            rerank_time_ms=rerank_latency,
            strategy_selection_time_ms=strategy_selection_time,
        )

        if options.log_metrics:
            await self.metrics_collector.log_metrics(metrics)

        # 6. Response構築
        metadata = RetrievalMetadata(
            strategy_used=strategy,
            query_intent=intent,
            total_latency_ms=total_latency,
            search_breakdown=search_latencies,
            num_results_before_rerank=num_before_rerank,
            num_results_after_rerank=len(final_results),
        )

        return RetrievalResponse(results=final_results, metadata=metadata)

    async def retrieve_with_context(
        self, query: str, context: Dict, options: Optional[RetrievalOptions] = None
    ) -> RetrievalResponse:
        """
        コンテキストを考慮した記憶検索

        Args:
            query: 検索クエリ
            context: 追加コンテキスト（前の会話、ユーザー属性など）
            options: 検索オプション

        Returns:
            RetrievalResponse: 検索結果 + メタデータ
        """
        # 基本的な検索を実行
        response = await self.retrieve(query, options)

        # Sprint 9: アクセスブーストを適用
        if self.scorer:
            import logging
            logger = logging.getLogger(__name__)
            for result in response.results:
                try:
                    # メモリIDを取得してアクセスブーストを適用
                    memory_id = str(result.id)
                    await self.scorer.boost_on_access(memory_id)
                except Exception as e:
                    logger.warning(f"Failed to boost memory {result.id}: {e}")

        return response

    def get_metrics_summary(self) -> Dict:
        """
        メトリクスサマリーを取得

        Returns:
            統計情報とパーセンタイル
        """
        stats = self.metrics_collector.get_statistics()
        percentiles = self.metrics_collector.get_latency_percentiles()

        return {
            "statistics": stats,
            "latency_percentiles": percentiles,
        }


def create_orchestrator(
    memory_store: MemoryStoreService,
    pool=None,
    embedding_service=None,
) -> RetrievalOrchestrator:
    """
    Orchestratorファクトリー関数

    Args:
        memory_store: Memory Store サービス
        pool: asyncpgコネクションプール（オプション）
        embedding_service: Embedding生成サービス（オプション）

    Returns:
        RetrievalOrchestrator: 設定済みのオーケストレーター
    """
    # コンポーネントの初期化
    query_analyzer = QueryAnalyzer()
    strategy_selector = StrategySelector()

    # 検索サービスの初期化
    keyword_searcher = None
    temporal_searcher = None

    if pool:
        keyword_searcher = KeywordSearcher(pool)
        if embedding_service:
            temporal_searcher = TemporalSearcher(pool, embedding_service)

    multi_search_executor = MultiSearchExecutor(
        memory_store=memory_store,
        keyword_searcher=keyword_searcher,
        temporal_searcher=temporal_searcher,
    )

    reranker = Reranker()
    metrics_collector = MetricsCollector()

    return RetrievalOrchestrator(
        query_analyzer=query_analyzer,
        strategy_selector=strategy_selector,
        multi_search_executor=multi_search_executor,
        reranker=reranker,
        metrics_collector=metrics_collector,
    )
