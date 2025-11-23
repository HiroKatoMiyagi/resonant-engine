"""
Query Analyzer - クエリ分析サービス

クエリを解析し、検索に必要なメタデータを抽出します。
「質問の呼吸を聴き取り、どの層を震わせるかを決める鼓膜」
"""

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict


class QueryType(str, Enum):
    """クエリタイプ"""

    FACTUAL = "factual"  # 事実確認 "〜はいつ？"
    CONCEPTUAL = "conceptual"  # 概念理解 "〜とは？"
    PROCEDURAL = "procedural"  # 手順確認 "〜はどうやる？"
    TEMPORAL = "temporal"  # 時系列 "最近の〜"
    COMPARATIVE = "comparative"  # 比較 "〜と〜の違い"


class TimeRange(BaseModel):
    """時間範囲"""

    start: Optional[datetime] = None
    end: Optional[datetime] = None
    relative: Optional[str] = None  # "last_week", "today", "yesterday", "this_month"

    # Pydantic V2 handles datetime serialization automatically


class QueryIntent(BaseModel):
    """クエリ意図"""

    query_type: QueryType
    keywords: List[str] = Field(default_factory=list)
    time_range: Optional[TimeRange] = None
    source_type_hint: Optional[str] = None
    importance: float = Field(default=0.5, ge=0.0, le=1.0)

    model_config = ConfigDict(use_enum_values=False)


class QueryAnalyzer:
    """
    クエリアナライザー

    クエリの意図を解析し、検索戦略の決定に必要なメタデータを抽出します。
    """

    # クエリタイプ判定用キーワード
    FACTUAL_KEYWORDS = [
        "いつ",
        "どこ",
        "誰",
        "何",
        "when",
        "where",
        "who",
        "what",
        "はどれ",
        "ですか",
    ]
    CONCEPTUAL_KEYWORDS = [
        "とは",
        "意味",
        "定義",
        "what is",
        "explain",
        "について",
        "概念",
        "理解",
    ]
    PROCEDURAL_KEYWORDS = [
        "どうやって",
        "方法",
        "手順",
        "how to",
        "やり方",
        "ステップ",
        "手続き",
    ]
    TEMPORAL_KEYWORDS = [
        "最近",
        "今日",
        "昨日",
        "先週",
        "今月",
        "今週",
        "recent",
        "today",
        "yesterday",
        "last week",
        "this month",
        "this week",
    ]
    COMPARATIVE_KEYWORDS = ["違い", "比較", "difference", "compare", "versus", "vs", "対比"]

    # ストップワード（日本語）
    STOPWORDS_JA = {
        "の",
        "は",
        "を",
        "に",
        "が",
        "と",
        "で",
        "や",
        "も",
        "へ",
        "から",
        "まで",
        "より",
        "など",
        "ます",
        "です",
        "こと",
        "もの",
        "ある",
        "いる",
        "する",
        "なる",
        "できる",
        "れる",
        "られる",
        "せる",
        "させる",
        "た",
        "て",
        "だ",
        "な",
    }

    # ストップワード（英語）
    STOPWORDS_EN = {
        "the",
        "a",
        "an",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "must",
        "shall",
        "can",
        "need",
        "dare",
        "ought",
        "used",
        "to",
        "of",
        "in",
        "for",
        "on",
        "with",
        "at",
        "by",
        "from",
        "up",
        "about",
        "into",
        "over",
        "after",
        "it",
        "its",
        "this",
        "that",
        "these",
        "those",
    }

    def analyze(self, query: str) -> QueryIntent:
        """
        クエリを解析

        Args:
            query: 検索クエリ

        Returns:
            QueryIntent: 解析結果
        """
        # クエリタイプ判定
        query_type = self._classify_query_type(query)

        # キーワード抽出
        keywords = self._extract_keywords(query)

        # 時間範囲抽出
        time_range = self._extract_time_range(query)

        # ソースタイプヒント推定
        source_type_hint = self._infer_source_type_hint(query)

        # 重要度判定
        importance = self._calculate_importance(query)

        return QueryIntent(
            query_type=query_type,
            keywords=keywords,
            time_range=time_range,
            source_type_hint=source_type_hint,
            importance=importance,
        )

    def _classify_query_type(self, query: str) -> QueryType:
        """クエリタイプ分類"""
        query_lower = query.lower()

        # ルールベース判定（優先度順）
        if any(kw in query_lower for kw in self.TEMPORAL_KEYWORDS):
            return QueryType.TEMPORAL

        if any(kw in query_lower for kw in self.COMPARATIVE_KEYWORDS):
            return QueryType.COMPARATIVE

        if any(kw in query_lower for kw in self.PROCEDURAL_KEYWORDS):
            return QueryType.PROCEDURAL

        if any(kw in query_lower for kw in self.FACTUAL_KEYWORDS):
            return QueryType.FACTUAL

        if any(kw in query_lower for kw in self.CONCEPTUAL_KEYWORDS):
            return QueryType.CONCEPTUAL

        # デフォルト: 概念的
        return QueryType.CONCEPTUAL

    def _extract_keywords(self, query: str) -> List[str]:
        """
        キーワード抽出（簡易実装）

        TODO: SpaCyで形態素解析を使用してより精度を上げる
        """
        # 基本的な文字区切り
        import re

        # 英数字、日本語文字を抽出
        words = re.findall(r"[a-zA-Z0-9]+|[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]+", query)

        # ストップワード除去
        filtered_words = []
        for word in words:
            word_lower = word.lower()
            if word_lower not in self.STOPWORDS_JA and word_lower not in self.STOPWORDS_EN:
                if len(word) > 1:  # 1文字は除外
                    filtered_words.append(word)

        return filtered_words

    def _extract_time_range(self, query: str) -> Optional[TimeRange]:
        """時間範囲抽出"""
        now = datetime.now(timezone.utc)
        query_lower = query.lower()

        if "今日" in query or "today" in query_lower:
            return TimeRange(
                start=now.replace(hour=0, minute=0, second=0, microsecond=0),
                end=now,
                relative="today",
            )

        if "昨日" in query or "yesterday" in query_lower:
            yesterday = now - timedelta(days=1)
            return TimeRange(
                start=yesterday.replace(hour=0, minute=0, second=0, microsecond=0),
                end=yesterday.replace(hour=23, minute=59, second=59, microsecond=999999),
                relative="yesterday",
            )

        if "先週" in query or "last week" in query_lower:
            week_ago = now - timedelta(days=7)
            return TimeRange(start=week_ago, end=now, relative="last_week")

        if "今週" in query or "this week" in query_lower:
            # 今週の月曜日から
            days_since_monday = now.weekday()
            monday = now - timedelta(days=days_since_monday)
            return TimeRange(
                start=monday.replace(hour=0, minute=0, second=0, microsecond=0),
                end=now,
                relative="this_week",
            )

        if "今月" in query or "this month" in query_lower:
            return TimeRange(
                start=now.replace(day=1, hour=0, minute=0, second=0, microsecond=0),
                end=now,
                relative="this_month",
            )

        if "最近" in query or "recent" in query_lower:
            # デフォルトで過去7日間
            return TimeRange(start=now - timedelta(days=7), end=now, relative="recent")

        return None

    def _infer_source_type_hint(self, query: str) -> Optional[str]:
        """ソースタイプヒントを推定"""
        query_lower = query.lower()

        if any(kw in query_lower for kw in ["意図", "intent", "質問", "question"]):
            return "intent"

        if any(kw in query_lower for kw in ["思考", "thought", "考え", "thinking"]):
            return "thought"

        if any(kw in query_lower for kw in ["修正", "correction", "訂正", "fix"]):
            return "correction"

        if any(kw in query_lower for kw in ["決定", "decision", "判断", "選択"]):
            return "decision"

        return None

    def _calculate_importance(self, query: str) -> float:
        """重要度を計算"""
        importance = 0.5  # ベースライン

        # 重要度を上げるキーワード
        high_importance_keywords = [
            "重要",
            "緊急",
            "critical",
            "important",
            "urgent",
            "必須",
            "essential",
            "危機",
            "crisis",
        ]

        # 重要度を下げるキーワード
        low_importance_keywords = ["参考", "optional", "maybe", "もしかして", "ついでに"]

        query_lower = query.lower()

        if any(kw in query_lower for kw in high_importance_keywords):
            importance = 0.8

        if any(kw in query_lower for kw in low_importance_keywords):
            importance = 0.3

        return importance
