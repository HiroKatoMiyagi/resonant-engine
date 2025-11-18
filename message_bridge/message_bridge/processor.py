import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class MessageProcessor:
    def __init__(self, pool, config):
        self.pool = pool
        self.config = config
        self.claude = None

        # Initialize Claude client if API key is available
        if config.get('anthropic_api_key'):
            try:
                import anthropic
                self.claude = anthropic.Anthropic(
                    api_key=config['anthropic_api_key']
                )
            except ImportError:
                logger.warning("Anthropic package not installed, using mock response")

    async def process(self, message_id):
        async with self.pool.acquire() as conn:
            # 1. Message取得
            message = await conn.fetchrow(
                "SELECT * FROM messages WHERE id = $1",
                message_id
            )

            if not message:
                logger.warning(f"⚠️ Message {message_id} not found")
                return

            # user typeのみ処理（無限ループ防止）
            if message['message_type'] != 'user':
                logger.info(f"⏭️ Skipping non-user message: {message['message_type']}")
                return

            try:
                # 2. Claude API呼び出し（またはモック）
                logger.info(f"🤖 Processing message from {message['user_id']}...")
                response = await self.call_claude(message['content'], message['user_id'])

                # 3. Kana応答をMessagesに保存
                await conn.execute("""
                    INSERT INTO messages (user_id, content, message_type, metadata)
                    VALUES ($1, $2, $3, $4::jsonb)
                """,
                    'kana',
                    response['response'],
                    'kana',
                    json.dumps(response.get('metadata', {}))
                )

                logger.info(f"✅ Message {message_id} processed successfully")

            except Exception as e:
                logger.error(f"Error processing message: {e}")
                # エラー時もシステムメッセージで応答
                await conn.execute("""
                    INSERT INTO messages (user_id, content, message_type, metadata)
                    VALUES ($1, $2, $3, $4::jsonb)
                """,
                    'kana',
                    f"申し訳ありません。処理中にエラーが発生しました: {str(e)}",
                    'kana',
                    json.dumps({"error": str(e), "original_message_id": str(message_id)})
                )
                logger.error(f"❌ Message {message_id} failed: {e}")

    async def call_claude(self, content, user_id):
        if self.claude:
            try:
                message = self.claude.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=4096,
                    messages=[{
                        "role": "user",
                        "content": f"""あなたはResonant EngineのKana（外界翻訳層）です。

ユーザー: {user_id}
メッセージ: {content}

以下のガイドラインで応答してください：
- 簡潔で明確な回答
- Resonant Engineの現在の機能を考慮
- 必要に応じて、YunoやTsumuとの連携を提案
- 技術的な質問には具体的に回答"""
                    }]
                )

                return {
                    "response": message.content[0].text,
                    "metadata": {
                        "model": message.model,
                        "usage": {
                            "input_tokens": message.usage.input_tokens,
                            "output_tokens": message.usage.output_tokens
                        },
                        "processed_at": datetime.utcnow().isoformat()
                    }
                }
            except Exception as e:
                logger.error(f"Claude API error: {e}")
                raise

        # Mock response when no API key
        response_text = self._generate_mock_response(content, user_id)
        return {
            "response": response_text,
            "metadata": {
                "model": "mock",
                "usage": {"input_tokens": 0, "output_tokens": 0},
                "processed_at": datetime.utcnow().isoformat()
            }
        }

    def _generate_mock_response(self, content, user_id):
        """モックモード用の応答生成"""
        content_lower = content.lower()

        # 質問パターンに応じた応答
        if "誰" in content or "だれ" in content:
            return """私はKana（外界翻訳層）です。現在、以下の機能が動作しています：

✅ **Intent Bridge**: Intentを自動処理し、Claude APIで応答を生成
✅ **Message Bridge**: メッセージに対する自動応答（今まさに動作中！）
✅ **PostgreSQL Dashboard**: メッセージ、Intent、通知の管理

Yunoは思想中枢、Tsumuは実装層として連携しています。"""

        elif "できる" in content or "機能" in content:
            return """現在のResonant Engineで動作している機能：

1. **メッセージ応答**: このように自動的にメッセージに応答します
2. **Intent処理**: タスクを作成すると自動的に処理・提案
3. **通知システム**: 処理完了時に自動通知
4. **仕様書管理**: PostgreSQLベースの仕様書システム

実装予定の機能：
- Claude Code統合（コード編集・実行）
- Memory System（コンテキスト記憶）
- Bridge Lite（意図抽出層）"""

        elif "ありがと" in content or "感謝" in content:
            return f"{user_id}さん、どういたしまして！何か他にお手伝いできることがあれば、お気軽にどうぞ。"

        elif "状態" in content or "ステータス" in content:
            return """**システムステータス** ✅

- PostgreSQL: 稼働中
- Intent Bridge: 稼働中
- Message Bridge: 稼働中（モックモード）
- Backend API: 稼働中
- Frontend: 稼働中

Claude APIキーを設定すると、本物のAI応答に切り替わります。"""

        else:
            return f"""メッセージを受け取りました: 「{content[:100]}」

私はKana（外界翻訳層）として、ユーザーの入力を理解し、適切な応答を生成します。

具体的な質問や指示があれば、より詳しくお答えできます。
例: 「機能は何ができる？」「Intentとは何？」など"""
