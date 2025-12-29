"""
Type and Project Inferencer - Automatic type and project inference

Infers memory type, project ID, and tags from event context and extracted meaning.
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from .models import (
    EmotionState,
    EventContext,
    InferenceResult,
    MemoryType,
    TypeInferenceRule,
)


class TypeProjectInferencer:
    """メモリタイプとプロジェクトIDの推論"""

    def __init__(self) -> None:
        """Initialize with default rules and patterns"""
        self.type_rules = self._load_type_rules()
        self.project_patterns = self._load_project_patterns()

    def infer(
        self, event: EventContext, extracted: Dict[str, Any]
    ) -> InferenceResult:
        """
        タイプとプロジェクトを推論

        Args:
            event: イベント文脈
            extracted: 抽出された意味情報

        Returns:
            推論結果
        """
        # タイプ推論
        memory_type, type_confidence, reasoning = self._infer_type(event, extracted)

        # プロジェクト推論
        project_id, project_confidence = self._infer_project(event, extracted)

        # タグ生成
        tags = self._generate_tags(event, extracted, memory_type)

        # 感情状態（既に抽出済み）
        emotion_state = extracted.get("emotion_state")

        return InferenceResult(
            memory_type=memory_type,
            confidence=type_confidence,
            reasoning=reasoning,
            project_id=project_id,
            project_confidence=project_confidence,
            tags=tags,
            emotion_state=emotion_state,
        )

    def _infer_type(
        self, event: EventContext, extracted: Dict[str, Any]
    ) -> Tuple[MemoryType, float, str]:
        """
        メモリタイプを推論

        Args:
            event: イベント文脈
            extracted: 抽出された意味情報

        Returns:
            (メモリタイプ, 信頼度, 推論理由) のタプル
        """
        intent_text = event.intent_text.lower()
        ci_level = extracted.get("ci_level", 0) or 0

        # CI Levelが非常に高い場合は最優先でCRISIS_LOG
        if ci_level >= 60:
            return (
                MemoryType.CRISIS_LOG,
                0.95,
                f"High CI level detected: {ci_level}",
            )

        # ルールベース推論（優先度順）
        for rule in sorted(self.type_rules, key=lambda r: r.priority, reverse=True):
            if self._match_pattern(intent_text, rule.pattern):
                return (
                    rule.memory_type,
                    0.9,
                    f"Pattern matched: {rule.description}",
                )

        # Intent typeに基づく推論
        intent_type_mapping = {
            "feature_request": MemoryType.SESSION_SUMMARY,
            "bug_fix": MemoryType.SESSION_SUMMARY,
            "exploration": MemoryType.SESSION_SUMMARY,
            "documentation": MemoryType.DESIGN_NOTE,
            "refactoring": MemoryType.DESIGN_NOTE,
            "testing": MemoryType.SESSION_SUMMARY,
        }

        if event.intent_type.lower() in intent_type_mapping:
            return (
                intent_type_mapping[event.intent_type.lower()],
                0.6,
                f"Inferred from intent type: {event.intent_type}",
            )

        # デフォルト: session_summary
        return (
            MemoryType.SESSION_SUMMARY,
            0.5,
            "Default classification",
        )

    def _infer_project(
        self, event: EventContext, extracted: Dict[str, Any]
    ) -> Tuple[Optional[str], float]:
        """
        プロジェクトIDを推論

        Args:
            event: イベント文脈
            extracted: 抽出された意味情報

        Returns:
            (プロジェクトID, 信頼度) のタプル
        """
        intent_text = event.intent_text.lower()

        # メタデータから直接取得（最高優先度）
        if event.metadata.get("project_id"):
            return event.metadata["project_id"], 1.0

        # パターンマッチング
        for project_id, patterns in self.project_patterns.items():
            for pattern in patterns:
                if pattern.lower() in intent_text:
                    return project_id, 0.85

        # タイトルからも検索
        title = extracted.get("title", "").lower()
        for project_id, patterns in self.project_patterns.items():
            for pattern in patterns:
                if pattern.lower() in title:
                    return project_id, 0.7

        return None, 0.0

    def _generate_tags(
        self,
        event: EventContext,
        extracted: Dict[str, Any],
        memory_type: MemoryType,
    ) -> List[str]:
        """
        タグを自動生成

        Args:
            event: イベント文脈
            extracted: 抽出された意味情報
            memory_type: 推論されたメモリタイプ

        Returns:
            生成されたタグのリスト
        """
        tags = []

        # タイプベースのタグ
        tags.append(memory_type.value)

        # 感情状態ベースのタグ
        emotion_state = extracted.get("emotion_state")
        if emotion_state:
            if isinstance(emotion_state, EmotionState):
                tags.append(emotion_state.value)
            else:
                tags.append(str(emotion_state))

        # Intent typeタグ
        if event.intent_type:
            tags.append(event.intent_type.lower().replace("_", "-"))

        # キーワード抽出
        keywords = self._extract_keywords(event.intent_text)
        tags.extend(keywords[:5])  # 最大5つ

        # 重複除去
        return list(set(tags))

    def _load_type_rules(self) -> List[TypeInferenceRule]:
        """
        タイプ推論ルールをロード

        Returns:
            推論ルールのリスト
        """
        return [
            TypeInferenceRule(
                pattern=r"(規範|regulation|ルール|原則|ポリシー|policy|guideline)",
                memory_type=MemoryType.RESONANT_REGULATION,
                priority=10,
                description="Regulation keywords detected",
            ),
            TypeInferenceRule(
                pattern=r"(マイルストーン|milestone|達成|完了した|完成|release|リリース)",
                memory_type=MemoryType.PROJECT_MILESTONE,
                priority=9,
                description="Milestone keywords detected",
            ),
            TypeInferenceRule(
                pattern=r"(設計|design|アーキテクチャ|architecture|構造|structure|パターン|pattern)",
                memory_type=MemoryType.DESIGN_NOTE,
                priority=8,
                description="Design keywords detected",
            ),
            TypeInferenceRule(
                pattern=r"(今日の振り返り|1日の|daily|日次|本日の|一日の)",
                memory_type=MemoryType.DAILY_REFLECTION,
                priority=7,
                description="Daily reflection keywords detected",
            ),
            TypeInferenceRule(
                pattern=r"(危機|crisis|緊急|urgent|エラー|error|障害|failure|問題|problem)",
                memory_type=MemoryType.CRISIS_LOG,
                priority=6,
                description="Crisis keywords detected",
            ),
            TypeInferenceRule(
                pattern=r"(セッション|session|作業|work|実装|implement|開発|develop)",
                memory_type=MemoryType.SESSION_SUMMARY,
                priority=5,
                description="Session keywords detected",
            ),
        ]

    def _load_project_patterns(self) -> Dict[str, List[str]]:
        """
        プロジェクトパターンをロード

        Returns:
            プロジェクトIDとパターンの辞書
        """
        return {
            "resonant_engine": [
                "resonant",
                "engine",
                "yuno",
                "kana",
                "tsumu",
                "呼吸",
                "bridge",
                "intent",
                "共鳴",
                "breathing",
            ],
            "postgres_implementation": [
                "postgresql",
                "postgres",
                "database",
                "db",
                "schema",
                "migration",
                "sql",
                "テーブル",
                "table",
            ],
            "memory_system": [
                "memory",
                "メモリ",
                "記憶",
                "semantic bridge",
                "semantic_bridge",
                "memory_item",
                "snapshot",
            ],
        }

    def _match_pattern(self, text: str, pattern: str) -> bool:
        """
        パターンマッチング

        Args:
            text: 検索対象テキスト
            pattern: 正規表現パターン

        Returns:
            マッチした場合True
        """
        try:
            return bool(re.search(pattern, text, re.IGNORECASE))
        except re.error:
            # 無効な正規表現の場合はリテラルマッチを試行
            return pattern.lower() in text.lower()

    def _extract_keywords(self, text: str) -> List[str]:
        """
        キーワード抽出（簡易版）

        Args:
            text: 抽出元テキスト

        Returns:
            抽出されたキーワードのリスト
        """
        keywords = []

        # 英単語の抽出（3文字以上）
        english_words = re.findall(r"\b[a-zA-Z]{3,}\b", text)
        for word in english_words:
            keyword = word.lower()
            # ストップワードを除外
            if keyword not in self._get_stop_words():
                keywords.append(keyword)

        # 日本語キーワードの抽出（カタカナ、漢字）
        japanese_keywords = re.findall(r"[\u30A0-\u30FF]{3,}|[\u4E00-\u9FFF]{2,}", text)
        keywords.extend(japanese_keywords)

        # 重複除去して返す
        seen = set()
        unique_keywords = []
        for kw in keywords:
            if kw not in seen:
                seen.add(kw)
                unique_keywords.append(kw)

        return unique_keywords[:10]  # 最大10個

    def _get_stop_words(self) -> set:
        """
        ストップワード集合を取得

        Returns:
            ストップワードの集合
        """
        return {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
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
