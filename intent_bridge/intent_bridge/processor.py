import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class IntentProcessor:
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

    async def process(self, intent_id):
        async with self.pool.acquire() as conn:
            # 1. Intent取得
            intent = await conn.fetchrow(
                "SELECT * FROM intents WHERE id = $1",
                intent_id
            )

            if not intent:
                logger.warning(f"⚠️ Intent {intent_id} not found")
                return

            # 2. ステータス更新: processing
            await conn.execute("""
                UPDATE intents
                SET status = 'processing', updated_at = NOW()
                WHERE id = $1
            """, intent_id)

            try:
                # 3. Claude API呼び出し（またはモック）
                logger.info(f"🤖 Processing intent...")
                response = await self.call_claude(intent['description'])

                # 4. 結果保存
                await conn.execute("""
                    UPDATE intents
                    SET status = 'completed',
                        result = $1::jsonb,
                        processed_at = NOW(),
                        updated_at = NOW()
                    WHERE id = $2
                """, json.dumps(response), intent_id)

                # 5. 通知作成
                await self.create_notification(conn, intent_id, 'success')

                logger.info(f"✅ Intent {intent_id} processed successfully")

            except Exception as e:
                logger.error(f"Error processing intent: {e}")
                await conn.execute("""
                    UPDATE intents
                    SET status = 'failed',
                        result = $1::jsonb,
                        updated_at = NOW()
                    WHERE id = $2
                """, json.dumps({"error": str(e)}), intent_id)

                await self.create_notification(conn, intent_id, 'error')
                logger.error(f"❌ Intent {intent_id} failed: {e}")

    async def call_claude(self, description):
        if self.claude:
            try:
                message = self.claude.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=4096,
                    messages=[{
                        "role": "user",
                        "content": f"""あなたはResonant EngineのKana（外界翻訳層）です。
以下のIntentを処理し、適切な応答を生成してください。

Intent: {description}

応答形式:
- 明確で構造化された回答
- 具体的なアクションアイテム（あれば）
- 次のステップの提案"""
                    }]
                )

                return {
                    "response": message.content[0].text,
                    "model": message.model,
                    "usage": {
                        "input_tokens": message.usage.input_tokens,
                        "output_tokens": message.usage.output_tokens
                    },
                    "processed_at": datetime.utcnow().isoformat()
                }
            except Exception as e:
                logger.error(f"Claude API error: {e}")
                raise

        # Mock response when no API key
        return {
            "response": f"[Mock Response] Intent processed: {description[:100]}",
            "model": "mock",
            "usage": {"input_tokens": 0, "output_tokens": 0},
            "processed_at": datetime.utcnow().isoformat()
        }

    async def create_notification(self, conn, intent_id, status):
        if status == 'success':
            title = "Intent処理完了"
            msg = f"Intent {str(intent_id)[:8]}... が正常に処理されました"
            notification_type = "success"
        else:
            title = "Intent処理失敗"
            msg = f"Intent {str(intent_id)[:8]}... の処理に失敗しました"
            notification_type = "error"

        await conn.execute("""
            INSERT INTO notifications (user_id, title, message, notification_type)
            VALUES ('hiroki', $1, $2, $3)
        """, title, msg, notification_type)
