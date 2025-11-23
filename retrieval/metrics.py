"""
Metrics Collector - メトリクス収集

検索品質と性能のメトリクスを収集します。
「呼吸の乱れを計測し、次の呼吸をより滑らかにするセンサー」
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, ConfigDict

from memory_store.models import MemoryResult

from .strategy import SearchStrategy


class SearchMetrics(BaseModel):
    """検索メトリクス"""

    query: str
    strategy: SearchStrategy
    total_latency_ms: float = Field(..., ge=0)
    search_latencies: Dict[str, float] = Field(default_factory=dict)
    num_results: int = Field(..., ge=0)
    avg_similarity: float = Field(..., ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # 追加メトリクス
    empty_results: bool = False
    rerank_time_ms: float = 0.0
    strategy_selection_time_ms: float = 0.0

    model_config = ConfigDict(use_enum_values=False)


class MetricsCollector:
    """
    メトリクス収集サービス

    検索の性能と品質を追跡し、モニタリングのためのデータを提供します。
    """

    def __init__(self):
        """メトリクスコレクターを初期化"""
        self._metrics_history: List[SearchMetrics] = []
        self._max_history_size = 1000  # 最大履歴サイズ

    async def collect(
        self,
        query: str,
        strategy: SearchStrategy,
        results: List[MemoryResult],
        latencies: Dict[str, float],
        rerank_time_ms: float = 0.0,
        strategy_selection_time_ms: float = 0.0,
    ) -> SearchMetrics:
        """
        メトリクス収集

        Args:
            query: 検索クエリ
            strategy: 使用した戦略
            results: 検索結果
            latencies: {検索手法: レイテンシ(ms)}
            rerank_time_ms: リランキング時間（ms）
            strategy_selection_time_ms: 戦略選択時間（ms）

        Returns:
            SearchMetrics: 収集されたメトリクス
        """
        avg_similarity = (
            sum(r.similarity for r in results) / len(results) if results else 0.0
        )

        total_latency = sum(latencies.values()) + rerank_time_ms + strategy_selection_time_ms

        metrics = SearchMetrics(
            query=query,
            strategy=strategy,
            total_latency_ms=total_latency,
            search_latencies=latencies,
            num_results=len(results),
            avg_similarity=avg_similarity,
            empty_results=len(results) == 0,
            rerank_time_ms=rerank_time_ms,
            strategy_selection_time_ms=strategy_selection_time_ms,
        )

        # 履歴に追加
        self._metrics_history.append(metrics)

        # 履歴サイズを制限
        if len(self._metrics_history) > self._max_history_size:
            self._metrics_history = self._metrics_history[-self._max_history_size :]

        return metrics

    async def log_metrics(self, metrics: SearchMetrics) -> None:
        """
        メトリクスをログ出力

        Args:
            metrics: 検索メトリクス
        """
        query_preview = metrics.query[:50] + "..." if len(metrics.query) > 50 else metrics.query

        print(
            f"""
        [Search Metrics]
        Query: {query_preview}
        Strategy: {metrics.strategy.value}
        Total Latency: {metrics.total_latency_ms:.2f}ms
        Results: {metrics.num_results}
        Avg Similarity: {metrics.avg_similarity:.3f}
        Breakdown: {metrics.search_latencies}
        Empty Results: {metrics.empty_results}
        Rerank Time: {metrics.rerank_time_ms:.2f}ms
        """
        )

    def get_statistics(self) -> Dict:
        """
        統計情報を取得

        Returns:
            統計情報の辞書
        """
        if not self._metrics_history:
            return {
                "total_searches": 0,
                "avg_latency_ms": 0.0,
                "avg_results": 0.0,
                "avg_similarity": 0.0,
                "empty_results_rate": 0.0,
                "strategy_distribution": {},
            }

        total_searches = len(self._metrics_history)

        # 平均レイテンシ
        avg_latency = sum(m.total_latency_ms for m in self._metrics_history) / total_searches

        # 平均結果数
        avg_results = sum(m.num_results for m in self._metrics_history) / total_searches

        # 平均類似度
        avg_similarity = sum(m.avg_similarity for m in self._metrics_history) / total_searches

        # 空結果率
        empty_count = sum(1 for m in self._metrics_history if m.empty_results)
        empty_rate = empty_count / total_searches

        # 戦略分布
        strategy_counts: Dict[str, int] = {}
        for m in self._metrics_history:
            strategy_name = m.strategy.value
            strategy_counts[strategy_name] = strategy_counts.get(strategy_name, 0) + 1

        strategy_distribution = {k: v / total_searches for k, v in strategy_counts.items()}

        return {
            "total_searches": total_searches,
            "avg_latency_ms": round(avg_latency, 2),
            "avg_results": round(avg_results, 2),
            "avg_similarity": round(avg_similarity, 3),
            "empty_results_rate": round(empty_rate, 4),
            "strategy_distribution": strategy_distribution,
        }

    def get_latency_percentiles(self) -> Dict[str, float]:
        """
        レイテンシのパーセンタイルを計算

        Returns:
            パーセンタイル情報
        """
        if not self._metrics_history:
            return {"p50": 0.0, "p90": 0.0, "p95": 0.0, "p99": 0.0}

        latencies = sorted([m.total_latency_ms for m in self._metrics_history])
        n = len(latencies)

        def percentile(p: float) -> float:
            index = int(n * p)
            if index >= n:
                index = n - 1
            return latencies[index]

        return {
            "p50": round(percentile(0.50), 2),
            "p90": round(percentile(0.90), 2),
            "p95": round(percentile(0.95), 2),
            "p99": round(percentile(0.99), 2),
        }

    def reset_history(self) -> None:
        """履歴をリセット"""
        self._metrics_history = []

    def export_metrics(self) -> List[Dict]:
        """
        メトリクスをエクスポート用にシリアライズ

        Returns:
            メトリクスのリスト
        """
        return [
            {
                "query": m.query,
                "strategy": m.strategy.value,
                "total_latency_ms": m.total_latency_ms,
                "search_latencies": m.search_latencies,
                "num_results": m.num_results,
                "avg_similarity": m.avg_similarity,
                "timestamp": m.timestamp.isoformat(),
                "empty_results": m.empty_results,
                "rerank_time_ms": m.rerank_time_ms,
            }
            for m in self._metrics_history
        ]
