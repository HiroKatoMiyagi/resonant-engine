import json
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


class IntentProcessor:
    def __init__(self, pool, config):
        self.pool = pool
        self.config = config
        self.claude = None
        self.claude_code_client = None

        # Initialize Claude API client if API key is available
        if config.get('anthropic_api_key'):
            try:
                import anthropic
                self.claude = anthropic.Anthropic(
                    api_key=config['anthropic_api_key']
                )
            except ImportError:
                logger.warning("Anthropic package not installed, using mock response")

        # Initialize Claude Code Client
        from .claude_code_client import ClaudeCodeClient
        self.claude_code_client = ClaudeCodeClient()

        # Initialize Intent Classifier
        from .classifier import IntentClassifier
        self.classifier = IntentClassifier()

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

            # 2. Intent分類
            intent_type = self.classifier.classify(intent['description'])
            classification_reason = self.classifier.get_classification_reason(intent['description'])

            logger.info(f"📋 Intent classified as: {intent_type}")
            logger.info(f"🔍 Reason: {classification_reason}")

            # 3. ステータス更新: processing
            await conn.execute("""
                UPDATE intents
                SET status = 'processing', updated_at = NOW()
                WHERE id = $1
            """, intent_id)

            try:
                # 4. Intent タイプに応じた処理
                if intent_type == 'code_execution':
                    # Claude Codeで処理
                    logger.info(f"⚙️  Processing with Claude Code...")
                    response = await self._process_with_claude_code(conn, intent)
                else:
                    # Claude APIで処理（従来通り）
                    logger.info(f"💬 Processing with Claude API...")
                    response = await self._process_with_claude_api(intent)

                # 5. 結果保存
                await conn.execute("""
                    UPDATE intents
                    SET status = 'completed',
                        result = $1::jsonb,
                        processed_at = NOW(),
                        updated_at = NOW()
                    WHERE id = $2
                """, json.dumps(response), intent_id)

                # 6. 通知作成
                await self.create_notification(conn, intent_id, 'success', intent_type)

                logger.info(f"✅ Intent {intent_id} processed successfully ({intent_type})")

            except Exception as e:
                logger.error(f"Error processing intent: {e}")
                await conn.execute("""
                    UPDATE intents
                    SET status = 'failed',
                        result = $1::jsonb,
                        updated_at = NOW()
                    WHERE id = $2
                """, json.dumps({"error": str(e)}), intent_id)

                await self.create_notification(conn, intent_id, 'error', intent_type)
                logger.error(f"❌ Intent {intent_id} failed: {e}")

    async def _process_with_claude_code(self, conn, intent) -> dict:
        """Claude Codeで処理"""
        start_time = datetime.now()

        # 1. セッション作成
        session_uuid = str(uuid.uuid4())
        session = await conn.fetchrow("""
            INSERT INTO claude_code_sessions (intent_id, session_id, status)
            VALUES ($1, $2, 'running')
            RETURNING *
        """, intent['id'], session_uuid)

        try:
            # 2. Claude Code実行
            logger.info(f"🚀 Starting Claude Code session: {session_uuid}")
            result = await self.claude_code_client.execute_task(
                task_description=intent['description'],
                context={
                    'workspace': '/tmp/resonant_workspace',
                    'files': []  # 必要に応じて追加
                },
                timeout=300
            )

            # 3. 実行履歴保存
            if result.get('executions'):
                for idx, execution in enumerate(result['executions']):
                    await conn.execute("""
                        INSERT INTO claude_code_executions
                        (session_id, execution_order, tool_name, input_data, output_data, success)
                        VALUES ($1, $2, $3, $4::jsonb, $5::jsonb, $6)
                    """,
                        session['id'],
                        idx,
                        execution.get('tool', 'Unknown'),
                        json.dumps(execution.get('input', {})),
                        json.dumps(execution.get('output', {})),
                        execution.get('success', True)
                    )

            # 4. セッション完了
            duration = (datetime.now() - start_time).total_seconds()
            await conn.execute("""
                UPDATE claude_code_sessions
                SET status = 'completed',
                    completed_at = NOW(),
                    total_duration_seconds = $1,
                    updated_at = NOW()
                WHERE id = $2
            """, int(duration), session['id'])

            return {
                'type': 'code_execution',
                'session_id': session_uuid,
                'output': result['output'],
                'file_changes': result.get('file_changes', []),
                'executions': result.get('executions', []),
                'success': result['success'],
                'mode': result.get('mode', 'unknown'),
                'duration_seconds': int(duration),
                'processed_at': datetime.utcnow().isoformat()
            }

        except Exception as e:
            # セッション失敗
            await conn.execute("""
                UPDATE claude_code_sessions
                SET status = 'failed',
                    error_message = $1,
                    completed_at = NOW(),
                    updated_at = NOW()
                WHERE id = $2
            """, str(e), session['id'])
            raise

    async def _process_with_claude_api(self, intent) -> dict:
        """Claude APIで処理（Sprint 4からの既存実装）"""
        if self.claude:
            try:
                message = self.claude.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=4096,
                    messages=[{
                        "role": "user",
                        "content": f"""あなたはResonant EngineのKana（外界翻訳層）です。
以下のIntentを処理し、適切な応答を生成してください。

Intent: {intent['description']}

応答形式:
- 明確で構造化された回答
- 具体的なアクションアイテム（あれば）
- 次のステップの提案"""
                    }]
                )

                return {
                    'type': 'chat',
                    'response': message.content[0].text,
                    'model': message.model,
                    'usage': {
                        'input_tokens': message.usage.input_tokens,
                        'output_tokens': message.usage.output_tokens
                    },
                    'processed_at': datetime.utcnow().isoformat()
                }
            except Exception as e:
                logger.error(f"Claude API error: {e}")
                raise

        # Mock response when no API key
        return {
            'type': 'chat',
            'response': f"[Mock Response] Intent processed: {intent['description'][:100]}",
            'model': 'mock',
            'usage': {'input_tokens': 0, 'output_tokens': 0},
            'processed_at': datetime.utcnow().isoformat()
        }

    async def create_notification(self, conn, intent_id, status, intent_type='unknown'):
        if status == 'success':
            type_label = {
                'chat': '💬 思考・提案',
                'code_execution': '⚙️ コード実行',
                'unknown': ''
            }.get(intent_type, '')

            title = f"Intent処理完了 {type_label}"
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
