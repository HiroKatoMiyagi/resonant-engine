"""
Semantic Extractor - Meaning extraction from events

Extracts semantic meaning from events including title generation,
content extraction, emotion inference, and metadata collection.
"""

from typing import Any, Dict, Optional

from .models import EmotionState, EventContext


class SemanticExtractor:
    """意味的分節化と文脈抽出"""

    def extract_meaning(self, event: EventContext) -> Dict[str, Any]:
        """
        イベントから意味を抽出

        Args:
            event: 処理対象のイベント文脈

        Returns:
            抽出された意味情報の辞書
        """
        return {
            "title": self._generate_title(event),
            "content": self._extract_content(event),
            "content_raw": event.intent_text,
            "ci_level": event.crisis_index,
            "emotion_state": self._infer_emotion(event),
            "started_at": event.timestamp,
            "metadata": self._extract_metadata(event),
        }

    def _generate_title(self, event: EventContext) -> str:
        """
        タイトル生成（要約的）

        Args:
            event: イベント文脈

        Returns:
            生成されたタイトル（最大50文字）
        """
        intent_text = event.intent_text.strip()

        # 短いテキストはそのまま返す
        if len(intent_text) <= 50:
            return intent_text

        # 最初の文を取得（日本語の句読点に対応）
        for separator in ["。", ".", "!", "！", "?", "？", "\n"]:
            if separator in intent_text:
                first_sentence = intent_text.split(separator)[0]
                if separator not in [".", "\n"]:
                    first_sentence += separator
                if len(first_sentence) <= 50:
                    return first_sentence.strip()

        # 50文字に切り詰める
        return intent_text[:47] + "..."

    def _extract_content(self, event: EventContext) -> str:
        """
        コンテンツ抽出

        Args:
            event: イベント文脈

        Returns:
            抽出されたコンテンツ
        """
        parts = [event.intent_text]

        # Kana応答があれば追加
        if event.kana_response:
            parts.append(f"\n【応答】\n{event.kana_response}")

        # Bridge結果があれば追加
        if event.bridge_result:
            result_summary = self._summarize_bridge_result(event.bridge_result)
            if result_summary:
                parts.append(f"\n【処理結果】\n{result_summary}")

        return "\n".join(parts)

    def _summarize_bridge_result(self, bridge_result: Dict[str, Any]) -> str:
        """
        Bridge処理結果を要約

        Args:
            bridge_result: Bridge処理結果

        Returns:
            要約文字列
        """
        if not bridge_result:
            return ""

        summary_parts = []

        # ステータス
        if "status" in bridge_result:
            summary_parts.append(f"Status: {bridge_result['status']}")

        # 処理時間
        if "processing_time_ms" in bridge_result:
            summary_parts.append(f"Processing: {bridge_result['processing_time_ms']}ms")

        # その他の重要な情報
        for key in ["action", "outcome", "error"]:
            if key in bridge_result:
                summary_parts.append(f"{key.capitalize()}: {bridge_result[key]}")

        return ", ".join(summary_parts) if summary_parts else ""

    def _infer_emotion(self, event: EventContext) -> Optional[EmotionState]:
        """
        感情状態の推論（Crisis Indexに基づく）

        Args:
            event: イベント文脈

        Returns:
            推論された感情状態
        """
        ci = event.crisis_index or 0

        if ci >= 70:
            return EmotionState.CRISIS
        elif ci >= 50:
            return EmotionState.STRESSED
        elif ci >= 30:
            return EmotionState.FOCUSED
        elif ci >= 10:
            return EmotionState.CALM
        else:
            return EmotionState.NEUTRAL

    def _extract_metadata(self, event: EventContext) -> Dict[str, Any]:
        """
        メタデータ抽出

        Args:
            event: イベント文脈

        Returns:
            抽出されたメタデータ
        """
        metadata = {
            "intent_id": str(event.intent_id),
            "intent_type": event.intent_type,
        }

        # セッションIDがあれば追加
        if event.session_id:
            metadata["session_id"] = str(event.session_id)

        # Bridge結果があれば追加
        if event.bridge_result:
            metadata["bridge_result"] = event.bridge_result

        # イベントのメタデータをマージ
        if event.metadata:
            metadata["event_metadata"] = event.metadata

        return metadata
