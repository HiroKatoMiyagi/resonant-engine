"""
Strategy Selector - 検索戦略の選択

クエリ意図に基づいて最適な検索戦略を決定します。
「意味と構造のバランスを取り、適切な共鳴モードを選ぶ指揮者」
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from .query_analyzer import QueryIntent, QueryType


class SearchStrategy(str, Enum):
    """検索戦略"""

    SEMANTIC_ONLY = "semantic_only"  # ベクトル検索のみ
    KEYWORD_BOOST = "keyword_boost"  # ベクトル + キーワード
    TEMPORAL = "temporal"  # 時系列 + ベクトル
    HYBRID = "hybrid"  # 全手法統合


class SearchParams(BaseModel):
    """検索パラメータ"""

    vector_weight: float = Field(default=0.7, ge=0.0, le=1.0)
    keyword_weight: float = Field(default=0.3, ge=0.0, le=1.0)
    limit: int = Field(default=10, ge=1, le=1000)
    similarity_threshold: float = Field(default=0.6, ge=0.0, le=1.0)
    time_decay_factor: float = Field(default=0.1, ge=0.0, le=1.0)

    class Config:
        validate_assignment = True


class StrategySelector:
    """
    戦略選択サービス

    クエリ意図に基づいて最適な検索戦略とパラメータを決定します。
    """

    def select_strategy(self, intent: QueryIntent) -> SearchStrategy:
        """
        クエリ意図から検索戦略を決定

        Args:
            intent: クエリ意図

        Returns:
            SearchStrategy: 選択された戦略
        """
        # 時間範囲指定あり → TEMPORAL
        if intent.time_range is not None:
            return SearchStrategy.TEMPORAL

        # 事実確認 + キーワードあり → KEYWORD_BOOST
        if intent.query_type == QueryType.FACTUAL and intent.keywords:
            return SearchStrategy.KEYWORD_BOOST

        # 概念理解 → SEMANTIC_ONLY
        if intent.query_type == QueryType.CONCEPTUAL:
            return SearchStrategy.SEMANTIC_ONLY

        # 手順確認 + キーワードあり → KEYWORD_BOOST
        if intent.query_type == QueryType.PROCEDURAL and intent.keywords:
            return SearchStrategy.KEYWORD_BOOST

        # 比較 → HYBRID（複数の観点が必要）
        if intent.query_type == QueryType.COMPARATIVE:
            return SearchStrategy.HYBRID

        # デフォルト: HYBRID
        return SearchStrategy.HYBRID

    def optimize_params(self, intent: QueryIntent, strategy: SearchStrategy) -> SearchParams:
        """
        戦略に応じてパラメータを最適化

        Args:
            intent: クエリ意図
            strategy: 検索戦略

        Returns:
            SearchParams: 最適化されたパラメータ
        """
        params = SearchParams()

        # SEMANTIC_ONLY: ベクトル検索のみを使用
        if strategy == SearchStrategy.SEMANTIC_ONLY:
            params.vector_weight = 1.0
            params.keyword_weight = 0.0
            params.similarity_threshold = 0.65  # 概念的な検索には少し厳しめ

        # KEYWORD_BOOST: キーワードの重みを上げる
        elif strategy == SearchStrategy.KEYWORD_BOOST:
            params.keyword_weight = 0.5
            params.vector_weight = 0.5
            params.similarity_threshold = 0.55  # キーワードマッチも考慮するので少し緩め

        # TEMPORAL: 時間減衰を調整
        elif strategy == SearchStrategy.TEMPORAL:
            if intent.time_range:
                if intent.time_range.relative == "today":
                    params.time_decay_factor = 0.0  # 今日のみ、減衰なし
                elif intent.time_range.relative == "yesterday":
                    params.time_decay_factor = 0.05
                elif intent.time_range.relative in ["this_week", "last_week", "recent"]:
                    params.time_decay_factor = 0.2
                else:
                    params.time_decay_factor = 0.3
            params.vector_weight = 0.8
            params.keyword_weight = 0.2

        # HYBRID: バランスの取れた設定
        elif strategy == SearchStrategy.HYBRID:
            params.vector_weight = 0.6
            params.keyword_weight = 0.4
            params.similarity_threshold = 0.5  # 多角的に検索するため緩め

        # 重要度に応じた調整
        if intent.importance > 0.7:
            params.limit = 20  # 重要なクエリは多めに取得
            params.similarity_threshold = max(
                0.4, params.similarity_threshold - 0.1
            )  # より多くの結果を含める

        if intent.importance < 0.4:
            params.limit = 5  # 重要度が低い場合は少なめ

        # ソースタイプヒントがある場合は類似度閾値を調整
        if intent.source_type_hint:
            # 特定のソースを探す場合はより厳しく
            params.similarity_threshold = min(
                0.8, params.similarity_threshold + 0.1
            )

        return params

    def get_strategy_description(self, strategy: SearchStrategy) -> str:
        """
        戦略の説明を取得

        Args:
            strategy: 検索戦略

        Returns:
            str: 戦略の説明
        """
        descriptions = {
            SearchStrategy.SEMANTIC_ONLY: "意味的類似度に基づく検索。概念的な質問に最適。",
            SearchStrategy.KEYWORD_BOOST: "ベクトル検索とキーワードマッチングの組み合わせ。固有名詞を含む質問に最適。",
            SearchStrategy.TEMPORAL: "時間範囲を考慮した検索。時系列の質問に最適。",
            SearchStrategy.HYBRID: "全ての検索手法を統合。複雑な複合クエリに最適。",
        }
        return descriptions.get(strategy, "Unknown strategy")
