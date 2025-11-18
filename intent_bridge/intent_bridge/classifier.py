"""
Intent Classifier - Intent振り分けロジック

IntentをClaude API（思考・提案）またはClaude Code（コード実行）に振り分ける
"""
from typing import Literal
import re

IntentType = Literal['chat', 'code_execution']


class IntentClassifier:
    """
    IntentをClaude APIまたはClaude Codeに振り分ける
    """

    # Claude Code実行が必要なキーワード
    CODE_EXECUTION_KEYWORDS = [
        # 実装系
        '実装して', '実装する', 'implement',
        'コードを書いて', 'コードを生成', 'code',
        'ファイルを編集', 'ファイル編集', 'edit',
        'ファイルを作成', 'ファイル作成', 'create file',

        # リファクタリング
        'リファクタリング', 'refactor', 'refactoring',
        '改善して', '最適化', 'optimize',

        # テスト・検証
        'テストを実行', 'テスト実行', 'run test', 'pytest',
        'テストを追加', 'テスト追加', 'add test',

        # Git操作
        'git commit', 'git push', 'git pull',
        'commit', 'push', 'pull request', 'pr',
        'prを作成', 'pr作成',

        # デプロイ・ビルド
        'デプロイ', 'deploy', 'build', 'ビルド',

        # バグ修正
        'バグを修正', 'バグ修正', 'fix bug', 'fix',
        'エラーを修正', 'エラー修正',

        # その他
        'スクリプトを実行', 'script', 'run',
    ]

    # ファイル拡張子パターン
    FILE_EXTENSION_PATTERN = re.compile(r'\.(py|js|ts|tsx|jsx|sql|sh|yaml|yml|json|md|txt|html|css)(\s|$|。|、)')

    # ファイルパスパターン
    FILE_PATH_PATTERN = re.compile(r'[/\\][\w/\\]+\.(py|js|ts|tsx|jsx|sql|sh|yaml|yml)')

    @classmethod
    def classify(cls, intent_description: str) -> IntentType:
        """
        Intent記述から処理タイプを判定

        Args:
            intent_description: Intentの説明文

        Returns:
            'chat': Claude APIで処理（思考・提案・質問応答）
            'code_execution': Claude Codeで処理（コード実行・編集）
        """
        description_lower = intent_description.lower()

        # 1. コード実行キーワードチェック
        for keyword in cls.CODE_EXECUTION_KEYWORDS:
            if keyword in description_lower:
                return 'code_execution'

        # 2. ファイル拡張子言及チェック
        if cls.FILE_EXTENSION_PATTERN.search(intent_description):
            return 'code_execution'

        # 3. ファイルパス言及チェック
        if cls.FILE_PATH_PATTERN.search(intent_description):
            return 'code_execution'

        # 4. 「〜してください」形式で具体的なアクションの場合
        if ('してください' in intent_description or 'して下さい' in intent_description):
            # 質問形式でなければcode_execution
            if not any(q in intent_description for q in ['？', '?', 'とは', 'って何', 'どう']):
                # ただし、説明・教育系は除外
                if not any(e in description_lower for e in ['教えて', '説明', 'とは', '理解したい', '知りたい']):
                    return 'code_execution'

        # デフォルトはチャット（思考・提案）
        return 'chat'

    @classmethod
    def get_classification_reason(cls, intent_description: str) -> str:
        """分類理由を返す（デバッグ用）"""
        description_lower = intent_description.lower()
        reasons = []

        for keyword in cls.CODE_EXECUTION_KEYWORDS:
            if keyword in description_lower:
                reasons.append(f"キーワード検出: '{keyword}'")

        if cls.FILE_EXTENSION_PATTERN.search(intent_description):
            match = cls.FILE_EXTENSION_PATTERN.search(intent_description)
            reasons.append(f"ファイル拡張子検出: {match.group()}")

        if cls.FILE_PATH_PATTERN.search(intent_description):
            match = cls.FILE_PATH_PATTERN.search(intent_description)
            reasons.append(f"ファイルパス検出: {match.group()}")

        if reasons:
            return ' | '.join(reasons)
        else:
            return 'デフォルト: チャット（思考・提案）'
