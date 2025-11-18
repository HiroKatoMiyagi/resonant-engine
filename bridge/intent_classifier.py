"""
Sprint 4.5: Intent分類ロジック
Intent記述からClaude APIまたはClaude Code実行を自動判定
"""
from typing import Literal
import re

IntentType = Literal['chat', 'code_execution']


class IntentClassifier:
    """
    Intent記述からClaude APIまたはClaude Code実行を判定
    """

    # Claude Code実行が必要なキーワード（日本語）
    CODE_EXECUTION_KEYWORDS = [
        # ファイル操作
        'ファイルを編集', 'ファイルを作成', 'ファイルを削除',
        'コードを追加', 'コードを修正', 'コードを削除',

        # コード生成
        'コードを生成', '関数を作成', 'クラスを作成',
        '実装して', 'コードを書いて',

        # リファクタリング
        'リファクタリング', 'リネーム', '整理して',

        # テスト・実行
        'テストを実行', 'テスト実行', 'テストして', 'pytest', 'unittest',
        'ビルド', 'デプロイ', 'run', 'test',

        # Git操作
        'git commit', 'git push', 'PRを作成',
        'コミット', 'プッシュ',

        # バグ修正
        'バグを修正', 'エラーを直して', 'デバッグ',

        # 英語キーワード
        'edit file', 'create file', 'implement',
        'refactor', 'fix bug', 'run test', 'write code',
        'generate code', 'add function'
    ]

    # ファイル拡張子パターン
    FILE_EXTENSION_PATTERN = re.compile(
        r'\.(py|js|ts|tsx|jsx|sql|sh|yaml|yml|json|md|txt|html|css|go|rs|java|cpp|c|h)(?:\s|$)',
        re.IGNORECASE
    )

    # ファイルパスパターン（例: src/main.py, bridge/intent_bridge.py）
    FILE_PATH_PATTERN = re.compile(
        r'(?:^|\s)[\w/]+\.[\w]+(?:\s|$)'
    )

    @classmethod
    def classify(cls, intent_description: str) -> IntentType:
        """
        Intent記述から処理タイプを判定

        Args:
            intent_description: Intentの説明文

        Returns:
            'chat': Claude APIで処理（質問応答、提案等）
            'code_execution': Claude Codeで処理（コード編集、実行等）
        """
        description_lower = intent_description.lower()

        # 1. コード実行キーワードチェック
        for keyword in cls.CODE_EXECUTION_KEYWORDS:
            if keyword.lower() in description_lower:
                return 'code_execution'

        # 2. ファイル拡張子チェック
        if cls.FILE_EXTENSION_PATTERN.search(intent_description):
            return 'code_execution'

        # 3. ファイルパスチェック（例: src/main.py）
        if cls.FILE_PATH_PATTERN.search(intent_description):
            return 'code_execution'

        # デフォルトはチャット（質問・提案等）
        return 'chat'

    @classmethod
    def get_confidence(cls, intent_description: str) -> float:
        """
        分類の信頼度を返す（0.0〜1.0）

        Returns:
            信頼度（高いほど確信が高い）
        """
        score = 0.0
        description_lower = intent_description.lower()

        # キーワードマッチ数
        keyword_matches = sum(
            1 for kw in cls.CODE_EXECUTION_KEYWORDS
            if kw.lower() in description_lower
        )
        score += min(keyword_matches * 0.2, 0.6)

        # ファイル拡張子
        if cls.FILE_EXTENSION_PATTERN.search(intent_description):
            score += 0.3

        # ファイルパス
        if cls.FILE_PATH_PATTERN.search(intent_description):
            score += 0.1

        return min(score, 1.0)


# テストコード
if __name__ == '__main__':
    # テストケース
    test_cases = [
        ("src/main.pyを編集して関数を追加", "code_execution"),
        ("testを実行してエラーを修正", "code_execution"),
        ("新しいAPIエンドポイントを実装して", "code_execution"),
        ("PostgreSQLのパフォーマンスについて教えて", "chat"),
        ("おすすめのアーキテクチャは？", "chat"),
        ("bridge/intent_classifier.pyを作成", "code_execution"),
        ("Sprint 4.5を実装して", "code_execution"),
    ]

    print("Intent分類テスト:")
    print("-" * 60)

    for description, expected in test_cases:
        result = IntentClassifier.classify(description)
        confidence = IntentClassifier.get_confidence(description)
        status = "✅" if result == expected else "❌"

        print(f"{status} Intent: {description}")
        print(f"   結果: {result} (期待: {expected})")
        print(f"   信頼度: {confidence:.2f}")
        print()

    print("-" * 60)
    print("テスト完了")
