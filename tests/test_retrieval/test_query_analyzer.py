"""
Query Analyzer Tests
"""

import pytest
from datetime import datetime, timezone

from retrieval.query_analyzer import QueryAnalyzer, QueryType, TimeRange, QueryIntent


@pytest.fixture
def analyzer():
    """QueryAnalyzerのフィクスチャ"""
    return QueryAnalyzer()


class TestQueryClassification:
    """クエリ分類のテスト"""

    def test_classify_factual_query_japanese(self, analyzer):
        """事実確認クエリの分類（日本語）"""
        intent = analyzer.analyze("Resonant Engineはいつ開始した？")
        assert intent.query_type == QueryType.FACTUAL

    def test_classify_factual_query_english(self, analyzer):
        """事実確認クエリの分類（英語）"""
        intent = analyzer.analyze("When did Resonant Engine start?")
        assert intent.query_type == QueryType.FACTUAL

    def test_classify_conceptual_query(self, analyzer):
        """概念理解クエリの分類"""
        intent = analyzer.analyze("呼吸リズムの意味について説明")
        assert intent.query_type == QueryType.CONCEPTUAL

    def test_classify_procedural_query(self, analyzer):
        """手順確認クエリの分類"""
        intent = analyzer.analyze("どうやってMemory Storeを設定する？")
        assert intent.query_type == QueryType.PROCEDURAL

    def test_classify_temporal_query(self, analyzer):
        """時系列クエリの分類"""
        intent = analyzer.analyze("最近のIntent")
        assert intent.query_type == QueryType.TEMPORAL

    def test_classify_comparative_query(self, analyzer):
        """比較クエリの分類"""
        intent = analyzer.analyze("Working MemoryとLong-term Memoryの違い")
        assert intent.query_type == QueryType.COMPARATIVE

    def test_default_conceptual(self, analyzer):
        """デフォルトは概念的"""
        intent = analyzer.analyze("Resonant Engine philosophy")
        assert intent.query_type == QueryType.CONCEPTUAL


class TestTimeRangeExtraction:
    """時間範囲抽出のテスト"""

    def test_extract_time_range_today(self, analyzer):
        """時間範囲抽出: 今日"""
        intent = analyzer.analyze("今日のIntent")
        assert intent.time_range is not None
        assert intent.time_range.relative == "today"
        assert intent.time_range.start is not None
        assert intent.time_range.end is not None

    def test_extract_time_range_yesterday(self, analyzer):
        """時間範囲抽出: 昨日"""
        intent = analyzer.analyze("昨日の記憶")
        assert intent.time_range is not None
        assert intent.time_range.relative == "yesterday"

    def test_extract_time_range_last_week(self, analyzer):
        """時間範囲抽出: 先週"""
        intent = analyzer.analyze("先週のDecision")
        assert intent.time_range is not None
        assert intent.time_range.relative == "last_week"

    def test_extract_time_range_this_week(self, analyzer):
        """時間範囲抽出: 今週"""
        intent = analyzer.analyze("今週のIntent")
        assert intent.time_range is not None
        assert intent.time_range.relative == "this_week"

    def test_extract_time_range_this_month(self, analyzer):
        """時間範囲抽出: 今月"""
        intent = analyzer.analyze("今月の記憶")
        assert intent.time_range is not None
        assert intent.time_range.relative == "this_month"

    def test_extract_time_range_recent(self, analyzer):
        """時間範囲抽出: 最近"""
        intent = analyzer.analyze("最近のThought")
        assert intent.time_range is not None
        assert intent.time_range.relative == "recent"

    def test_no_time_range(self, analyzer):
        """時間範囲なし"""
        intent = analyzer.analyze("呼吸のリズムとは")
        assert intent.time_range is None


class TestKeywordExtraction:
    """キーワード抽出のテスト"""

    def test_extract_keywords_japanese(self, analyzer):
        """日本語キーワード抽出"""
        intent = analyzer.analyze("Resonant Engineの設計原則")
        assert "Resonant" in intent.keywords
        assert "Engine" in intent.keywords
        # 「設計原則」は分割されないため、個別の単語として扱われる
        assert any("設計" in kw or "原則" in kw for kw in intent.keywords)

    def test_extract_keywords_english(self, analyzer):
        """英語キーワード抽出"""
        intent = analyzer.analyze("Memory Store architecture design")
        assert "Memory" in intent.keywords
        assert "Store" in intent.keywords
        assert "architecture" in intent.keywords
        assert "design" in intent.keywords

    def test_stopwords_removed(self, analyzer):
        """ストップワードが除去される"""
        intent = analyzer.analyze("the Memory is stored in database")
        assert "the" not in intent.keywords
        assert "is" not in intent.keywords
        assert "in" not in intent.keywords
        assert "Memory" in intent.keywords
        assert "stored" in intent.keywords


class TestImportanceCalculation:
    """重要度計算のテスト"""

    def test_high_importance(self, analyzer):
        """高重要度"""
        intent = analyzer.analyze("重要なIntent情報を取得")
        assert intent.importance == 0.8

    def test_critical_importance(self, analyzer):
        """危機的重要度"""
        intent = analyzer.analyze("crisis index exceeded threshold")
        assert intent.importance == 0.8

    def test_low_importance(self, analyzer):
        """低重要度"""
        intent = analyzer.analyze("参考までに確認")
        assert intent.importance == 0.3

    def test_default_importance(self, analyzer):
        """デフォルト重要度"""
        intent = analyzer.analyze("呼吸のリズム")
        assert intent.importance == 0.5


class TestSourceTypeHint:
    """ソースタイプヒントのテスト"""

    def test_intent_hint(self, analyzer):
        """Intentヒント"""
        intent = analyzer.analyze("ユーザーのintentを確認")
        assert intent.source_type_hint == "intent"

    def test_thought_hint(self, analyzer):
        """Thoughtヒント"""
        intent = analyzer.analyze("私の思考プロセス")
        assert intent.source_type_hint == "thought"

    def test_decision_hint(self, analyzer):
        """Decisionヒント"""
        intent = analyzer.analyze("判断の記録")
        assert intent.source_type_hint == "decision"

    def test_no_hint(self, analyzer):
        """ヒントなし"""
        intent = analyzer.analyze("Resonant Engine")
        assert intent.source_type_hint is None
