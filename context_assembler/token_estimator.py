"""Token Estimator - トークン数推定"""

from typing import Dict, List


class TokenEstimator:
    """
    トークン数推定クラス

    簡易推定ロジック:
    - 日本語1文字 ≈ 2トークン
    - 英語1文字 ≈ 0.5トークン
    - メッセージ構造オーバーヘッド: 10トークン/メッセージ
    """

    def estimate(self, messages: List[Dict[str, str]]) -> int:
        """
        メッセージリストのトークン数を推定

        Args:
            messages: Claude API形式のメッセージリスト

        Returns:
            推定トークン数
        """
        total = 0

        for msg in messages:
            content = msg.get("content", "")

            # 日本語文字数（UnicodeのCJK範囲）
            japanese_chars = sum(
                1
                for c in content
                if 0x3000 <= ord(c) <= 0x9FFF or 0xFF00 <= ord(c) <= 0xFFEF
            )

            # その他の文字数
            other_chars = len(content) - japanese_chars

            # 推定
            total += japanese_chars * 2
            total += other_chars * 0.5

            # メッセージ構造オーバーヘッド
            total += 10

        return int(total)

    def estimate_string(self, text: str) -> int:
        """
        単一文字列のトークン数を推定

        Args:
            text: 推定対象のテキスト

        Returns:
            推定トークン数
        """
        japanese_chars = sum(
            1
            for c in text
            if 0x3000 <= ord(c) <= 0x9FFF or 0xFF00 <= ord(c) <= 0xFFEF
        )
        other_chars = len(text) - japanese_chars

        return int(japanese_chars * 2 + other_chars * 0.5)
