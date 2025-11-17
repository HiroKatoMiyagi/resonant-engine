"""
Orchestrator Integration Tests
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from retrieval.orchestrator import (
    RetrievalOrchestrator,
    RetrievalOptions,
    create_orchestrator,
)
from retrieval.query_analyzer import QueryAnalyzer
from retrieval.strategy import StrategySelector, SearchStrategy
from retrieval.multi_search import MultiSearchExecutor
from retrieval.reranker import Reranker
from retrieval.metrics import MetricsCollector
from memory_store.models import MemoryResult, MemoryType


@pytest.fixture
def mock_memory_store():
    """Mock Memory Store"""
    store = AsyncMock()
    store.search_similar = AsyncMock(return_value=[])
    return store


@pytest.fixture
def orchestrator(mock_memory_store):
    """Orchestratorのフィクスチャ"""
    return create_orchestrator(mock_memory_store)


@pytest.fixture
def sample_memory_results():
    """サンプル記憶結果"""
    now = datetime.now(timezone.utc)
    return [
        MemoryResult(
            id=1,
            content="Resonant Engineは呼吸のリズムで動作する",
            memory_type=MemoryType.LONGTERM,
            similarity=0.85,
            created_at=now,
            metadata={"tags": ["philosophy"]},
        ),
        MemoryResult(
            id=2,
            content="Memory Storeはpgvectorを使用",
            memory_type=MemoryType.LONGTERM,
            similarity=0.75,
            created_at=now,
            metadata={"tags": ["technical"]},
        ),
    ]


class TestOrchestratorIntegration:
    """Orchestrator統合テスト"""

    @pytest.mark.asyncio
    async def test_full_retrieval_flow(self, orchestrator, mock_memory_store, sample_memory_results):
        """E2Eテスト: 完全な検索フロー"""
        mock_memory_store.search_similar.return_value = sample_memory_results

        response = await orchestrator.retrieve(query="呼吸について教えて")

        # 検証
        assert len(response.results) > 0
        assert response.metadata.strategy_used in [
            SearchStrategy.SEMANTIC_ONLY,
            SearchStrategy.KEYWORD_BOOST,
            SearchStrategy.HYBRID,
        ]
        assert response.metadata.total_latency_ms >= 0

    @pytest.mark.asyncio
    async def test_force_strategy(self, orchestrator, mock_memory_store, sample_memory_results):
        """戦略強制指定"""
        mock_memory_store.search_similar.return_value = sample_memory_results

        response = await orchestrator.retrieve(
            query="テストクエリ",
            options=RetrievalOptions(force_strategy=SearchStrategy.KEYWORD_BOOST),
        )

        assert response.metadata.strategy_used == SearchStrategy.KEYWORD_BOOST

    @pytest.mark.asyncio
    async def test_custom_limit(self, orchestrator, mock_memory_store):
        """カスタムlimit"""
        now = datetime.now(timezone.utc)
        results = [
            MemoryResult(
                id=i,
                content=f"Memory {i}",
                memory_type=MemoryType.LONGTERM,
                similarity=0.9 - i * 0.02,
                created_at=now,
                metadata={},
            )
            for i in range(20)
        ]
        mock_memory_store.search_similar.return_value = results

        response = await orchestrator.retrieve(
            query="テストクエリ", options=RetrievalOptions(limit=5)
        )

        assert len(response.results) <= 5

    @pytest.mark.asyncio
    async def test_empty_results(self, orchestrator, mock_memory_store):
        """空の検索結果"""
        mock_memory_store.search_similar.return_value = []

        response = await orchestrator.retrieve(query="存在しないデータ")

        assert len(response.results) == 0
        assert response.metadata.num_results_after_rerank == 0

    @pytest.mark.asyncio
    async def test_metadata_details(self, orchestrator, mock_memory_store, sample_memory_results):
        """メタデータ詳細"""
        mock_memory_store.search_similar.return_value = sample_memory_results

        response = await orchestrator.retrieve(
            query="呼吸のリズム", options=RetrievalOptions(include_metadata_details=True)
        )

        # メタデータが含まれている
        assert response.metadata.query_intent is not None
        assert response.metadata.search_breakdown is not None

    @pytest.mark.asyncio
    async def test_temporal_query_strategy_selection(self, orchestrator, mock_memory_store, sample_memory_results):
        """時系列クエリで正しい戦略が選択される"""
        mock_memory_store.search_similar.return_value = sample_memory_results

        response = await orchestrator.retrieve(query="今日のIntent")

        # 時間範囲が指定されているのでTEMPORAL戦略が選択される
        assert response.metadata.strategy_used == SearchStrategy.TEMPORAL
        assert response.metadata.query_intent.time_range is not None
        assert response.metadata.query_intent.time_range.relative == "today"

    @pytest.mark.asyncio
    async def test_conceptual_query_strategy_selection(self, orchestrator, mock_memory_store, sample_memory_results):
        """概念的クエリで正しい戦略が選択される"""
        mock_memory_store.search_similar.return_value = sample_memory_results

        response = await orchestrator.retrieve(query="呼吸リズムの意味について説明")

        assert response.metadata.strategy_used == SearchStrategy.SEMANTIC_ONLY

    @pytest.mark.asyncio
    async def test_factual_query_with_keywords_strategy_selection(
        self, orchestrator, mock_memory_store, sample_memory_results
    ):
        """事実確認クエリで正しい戦略が選択される"""
        mock_memory_store.search_similar.return_value = sample_memory_results

        response = await orchestrator.retrieve(query="Resonant Engineはいつ開始した")

        assert response.metadata.strategy_used == SearchStrategy.KEYWORD_BOOST


class TestMetricsCollection:
    """メトリクス収集のテスト"""

    @pytest.mark.asyncio
    async def test_metrics_collected(self, orchestrator, mock_memory_store, sample_memory_results):
        """メトリクスが収集される"""
        mock_memory_store.search_similar.return_value = sample_memory_results

        await orchestrator.retrieve(query="テスト")

        stats = orchestrator.get_metrics_summary()
        assert stats["statistics"]["total_searches"] == 1

    @pytest.mark.asyncio
    async def test_metrics_summary(self, orchestrator, mock_memory_store, sample_memory_results):
        """メトリクスサマリー"""
        mock_memory_store.search_similar.return_value = sample_memory_results

        # 複数回検索
        for _ in range(5):
            await orchestrator.retrieve(query="テスト", options=RetrievalOptions(log_metrics=False))

        summary = orchestrator.get_metrics_summary()

        assert summary["statistics"]["total_searches"] == 5
        assert "avg_latency_ms" in summary["statistics"]
        assert "p95" in summary["latency_percentiles"]

    @pytest.mark.asyncio
    async def test_empty_results_rate(self, orchestrator, mock_memory_store):
        """空結果率の追跡"""
        mock_memory_store.search_similar.return_value = []

        for _ in range(3):
            await orchestrator.retrieve(query="存在しない", options=RetrievalOptions(log_metrics=False))

        stats = orchestrator.get_metrics_summary()["statistics"]
        assert stats["empty_results_rate"] == 1.0

    @pytest.mark.asyncio
    async def test_disable_metrics_logging(self, orchestrator, mock_memory_store, sample_memory_results):
        """メトリクスログの無効化"""
        mock_memory_store.search_similar.return_value = sample_memory_results

        # log_metrics=Falseでもメトリクスは収集される
        response = await orchestrator.retrieve(
            query="テスト", options=RetrievalOptions(log_metrics=False)
        )

        assert response is not None
        stats = orchestrator.get_metrics_summary()
        assert stats["statistics"]["total_searches"] >= 1


class TestSearchStrategies:
    """検索戦略のテスト"""

    @pytest.mark.asyncio
    async def test_semantic_only_strategy(self, orchestrator, mock_memory_store, sample_memory_results):
        """SEMANTIC_ONLY戦略"""
        mock_memory_store.search_similar.return_value = sample_memory_results

        response = await orchestrator.retrieve(
            query="テスト", options=RetrievalOptions(force_strategy=SearchStrategy.SEMANTIC_ONLY)
        )

        # ベクトル検索のみが使用される
        assert "vector" in response.metadata.search_breakdown or len(response.metadata.search_breakdown) > 0

    @pytest.mark.asyncio
    async def test_hybrid_strategy(self, orchestrator, mock_memory_store, sample_memory_results):
        """HYBRID戦略"""
        mock_memory_store.search_similar.return_value = sample_memory_results

        response = await orchestrator.retrieve(
            query="テスト", options=RetrievalOptions(force_strategy=SearchStrategy.HYBRID)
        )

        assert response.metadata.strategy_used == SearchStrategy.HYBRID


class TestPerformance:
    """性能テスト"""

    @pytest.mark.asyncio
    async def test_retrieval_latency_acceptable(self, orchestrator, mock_memory_store, sample_memory_results):
        """検索レイテンシが許容範囲内"""
        mock_memory_store.search_similar.return_value = sample_memory_results

        response = await orchestrator.retrieve(query="テストクエリ")

        # 200ms以内（モックなので非常に速い）
        assert response.metadata.total_latency_ms < 200

    @pytest.mark.asyncio
    async def test_reranking_count(self, orchestrator, mock_memory_store):
        """リランキング前後の件数"""
        now = datetime.now(timezone.utc)
        results = [
            MemoryResult(
                id=i,
                content=f"Memory {i}",
                memory_type=MemoryType.LONGTERM,
                similarity=0.9 - i * 0.01,
                created_at=now,
                metadata={},
            )
            for i in range(20)
        ]
        mock_memory_store.search_similar.return_value = results

        response = await orchestrator.retrieve(query="テスト", options=RetrievalOptions(limit=10))

        assert response.metadata.num_results_before_rerank >= response.metadata.num_results_after_rerank
        assert response.metadata.num_results_after_rerank <= 10


class TestQueryIntentAnalysis:
    """クエリ意図分析のテスト"""

    @pytest.mark.asyncio
    async def test_high_importance_query(self, orchestrator, mock_memory_store, sample_memory_results):
        """高重要度クエリ"""
        mock_memory_store.search_similar.return_value = sample_memory_results

        response = await orchestrator.retrieve(query="重要なIntent情報を取得")

        assert response.metadata.query_intent.importance > 0.7

    @pytest.mark.asyncio
    async def test_keyword_extraction(self, orchestrator, mock_memory_store, sample_memory_results):
        """キーワード抽出"""
        mock_memory_store.search_similar.return_value = sample_memory_results

        response = await orchestrator.retrieve(query="Resonant Engine Memory Store")

        keywords = response.metadata.query_intent.keywords
        assert "Resonant" in keywords
        assert "Engine" in keywords
        assert "Memory" in keywords
        assert "Store" in keywords

    @pytest.mark.asyncio
    async def test_time_range_extraction(self, orchestrator, mock_memory_store, sample_memory_results):
        """時間範囲抽出"""
        mock_memory_store.search_similar.return_value = sample_memory_results

        response = await orchestrator.retrieve(query="先週の記憶")

        assert response.metadata.query_intent.time_range is not None
        assert response.metadata.query_intent.time_range.relative == "last_week"


class TestErrorHandling:
    """エラーハンドリングのテスト"""

    @pytest.mark.asyncio
    async def test_search_failure_graceful_handling(self, orchestrator, mock_memory_store):
        """検索失敗時の適切なハンドリング"""
        mock_memory_store.search_similar.side_effect = Exception("Database error")

        # 例外が発生してもクラッシュしない
        response = await orchestrator.retrieve(query="テスト")

        # 空の結果が返される
        assert len(response.results) == 0

    @pytest.mark.asyncio
    async def test_invalid_options_handled(self, orchestrator, mock_memory_store, sample_memory_results):
        """無効なオプションのハンドリング"""
        mock_memory_store.search_similar.return_value = sample_memory_results

        # オプションなしでも動作する
        response = await orchestrator.retrieve(query="テスト", options=None)

        assert response is not None
