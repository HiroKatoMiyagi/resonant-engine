"""
Strategy Selector Tests
"""

import pytest

from retrieval.strategy import StrategySelector, SearchStrategy, SearchParams
from retrieval.query_analyzer import QueryIntent, QueryType, TimeRange


@pytest.fixture
def selector():
    """StrategySelectorのフィクスチャ"""
    return StrategySelector()


class TestStrategySelection:
    """戦略選択のテスト"""

    def test_select_semantic_strategy(self, selector):
        """概念理解 → SEMANTIC_ONLY"""
        intent = QueryIntent(query_type=QueryType.CONCEPTUAL, keywords=["呼吸", "リズム"])
        strategy = selector.select_strategy(intent)
        assert strategy == SearchStrategy.SEMANTIC_ONLY

    def test_select_temporal_strategy(self, selector):
        """時間範囲指定 → TEMPORAL"""
        intent = QueryIntent(
            query_type=QueryType.FACTUAL,
            keywords=["Intent"],
            time_range=TimeRange(relative="today"),
        )
        strategy = selector.select_strategy(intent)
        assert strategy == SearchStrategy.TEMPORAL

    def test_select_keyword_boost_strategy(self, selector):
        """事実確認 + キーワード → KEYWORD_BOOST"""
        intent = QueryIntent(query_type=QueryType.FACTUAL, keywords=["Resonant", "Engine"])
        strategy = selector.select_strategy(intent)
        assert strategy == SearchStrategy.KEYWORD_BOOST

    def test_select_hybrid_strategy(self, selector):
        """比較 → HYBRID"""
        intent = QueryIntent(query_type=QueryType.COMPARATIVE, keywords=["Memory", "Store"])
        strategy = selector.select_strategy(intent)
        assert strategy == SearchStrategy.HYBRID

    def test_procedural_with_keywords(self, selector):
        """手順確認 + キーワード → KEYWORD_BOOST"""
        intent = QueryIntent(query_type=QueryType.PROCEDURAL, keywords=["setup", "config"])
        strategy = selector.select_strategy(intent)
        assert strategy == SearchStrategy.KEYWORD_BOOST

    def test_temporal_overrides_factual(self, selector):
        """時間範囲指定は事実確認より優先"""
        intent = QueryIntent(
            query_type=QueryType.FACTUAL,
            keywords=["Intent"],
            time_range=TimeRange(relative="yesterday"),
        )
        strategy = selector.select_strategy(intent)
        assert strategy == SearchStrategy.TEMPORAL


class TestParameterOptimization:
    """パラメータ最適化のテスト"""

    def test_optimize_params_semantic_only(self, selector):
        """SEMANTIC_ONLY時のパラメータ最適化"""
        intent = QueryIntent(query_type=QueryType.CONCEPTUAL, keywords=[])
        strategy = SearchStrategy.SEMANTIC_ONLY
        params = selector.optimize_params(intent, strategy)

        assert params.vector_weight == 1.0
        assert params.keyword_weight == 0.0
        assert params.similarity_threshold == 0.65

    def test_optimize_params_keyword_boost(self, selector):
        """KEYWORD_BOOST時のパラメータ最適化"""
        intent = QueryIntent(query_type=QueryType.FACTUAL, keywords=["Resonant", "Engine"])
        strategy = SearchStrategy.KEYWORD_BOOST
        params = selector.optimize_params(intent, strategy)

        assert params.keyword_weight == 0.5
        assert params.vector_weight == 0.5
        assert params.similarity_threshold == 0.55

    def test_optimize_params_temporal_today(self, selector):
        """TEMPORAL（今日）時のパラメータ最適化"""
        intent = QueryIntent(
            query_type=QueryType.TEMPORAL,
            keywords=["Intent"],
            time_range=TimeRange(relative="today"),
        )
        strategy = SearchStrategy.TEMPORAL
        params = selector.optimize_params(intent, strategy)

        assert params.time_decay_factor == 0.0
        assert params.vector_weight == 0.8
        assert params.keyword_weight == 0.2

    def test_optimize_params_temporal_last_week(self, selector):
        """TEMPORAL（先週）時のパラメータ最適化"""
        intent = QueryIntent(
            query_type=QueryType.TEMPORAL,
            keywords=["Intent"],
            time_range=TimeRange(relative="last_week"),
        )
        strategy = SearchStrategy.TEMPORAL
        params = selector.optimize_params(intent, strategy)

        assert params.time_decay_factor == 0.2

    def test_optimize_params_hybrid(self, selector):
        """HYBRID時のパラメータ最適化"""
        intent = QueryIntent(query_type=QueryType.COMPARATIVE, keywords=["A", "B"])
        strategy = SearchStrategy.HYBRID
        params = selector.optimize_params(intent, strategy)

        assert params.vector_weight == 0.6
        assert params.keyword_weight == 0.4
        assert params.similarity_threshold == 0.5

    def test_high_importance_increases_limit(self, selector):
        """高重要度はlimitを増加"""
        intent = QueryIntent(query_type=QueryType.CONCEPTUAL, keywords=[], importance=0.8)
        strategy = SearchStrategy.SEMANTIC_ONLY
        params = selector.optimize_params(intent, strategy)

        assert params.limit == 20

    def test_low_importance_decreases_limit(self, selector):
        """低重要度はlimitを減少"""
        intent = QueryIntent(query_type=QueryType.CONCEPTUAL, keywords=[], importance=0.3)
        strategy = SearchStrategy.SEMANTIC_ONLY
        params = selector.optimize_params(intent, strategy)

        assert params.limit == 5

    def test_source_type_hint_increases_threshold(self, selector):
        """ソースタイプヒントは閾値を増加"""
        intent = QueryIntent(
            query_type=QueryType.CONCEPTUAL, keywords=[], source_type_hint="decision"
        )
        strategy = SearchStrategy.SEMANTIC_ONLY
        params = selector.optimize_params(intent, strategy)

        # 元の閾値 0.65 + 0.1 = 0.75
        assert params.similarity_threshold == 0.75


class TestStrategyDescription:
    """戦略説明のテスト"""

    def test_get_semantic_only_description(self, selector):
        """SEMANTIC_ONLYの説明"""
        desc = selector.get_strategy_description(SearchStrategy.SEMANTIC_ONLY)
        assert "意味的" in desc or "概念" in desc

    def test_get_keyword_boost_description(self, selector):
        """KEYWORD_BOOSTの説明"""
        desc = selector.get_strategy_description(SearchStrategy.KEYWORD_BOOST)
        assert "キーワード" in desc or "固有名詞" in desc

    def test_get_temporal_description(self, selector):
        """TEMPORALの説明"""
        desc = selector.get_strategy_description(SearchStrategy.TEMPORAL)
        assert "時間" in desc or "時系列" in desc

    def test_get_hybrid_description(self, selector):
        """HYBRIDの説明"""
        desc = selector.get_strategy_description(SearchStrategy.HYBRID)
        assert "統合" in desc or "全て" in desc
