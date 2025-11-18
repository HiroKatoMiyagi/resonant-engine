"""
Sprint 4 + 4.5: Intent Bridge統合版
PostgreSQL LISTEN/NOTIFYでIntent自動検知し、Claude API/Claude Codeで処理
"""
import asyncio
import asyncpg
import anthropic
from datetime import datetime
import json
import uuid
import os
from typing import Dict, Any, Optional, List
import logging

# Sprint 4.5モジュール
from intent_classifier import IntentClassifier
from context_loader import ContextLoader
from claude_code_client import ClaudeCodeClient


# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class IntentBridge:
    """
    Intent自動処理デーモン

    機能：
    - PostgreSQL LISTEN/NOTIFYでIntent検知
    - Intent分類（Claude API vs Claude Code）
    - コンテキスト自動ロード
    - DB記憶統合（過去Intent参照）
    - 処理結果保存
    - 通知生成
    """

    def __init__(
        self,
        db_config: Optional[Dict[str, str]] = None,
        workspace_mode: str = 'repository'
    ):
        self.pool: Optional[asyncpg.Pool] = None
        self.running = False

        # Sprint 4: Claude API
        self.claude_api = anthropic.Anthropic(
            api_key=os.getenv('ANTHROPIC_API_KEY')
        )

        # Sprint 4.5: Intent分類、コンテキストローダー、Claude Code Client
        self.classifier = IntentClassifier()
        self.context_loader = ContextLoader()
        self.claude_code = ClaudeCodeClient(workspace_mode=workspace_mode)

        # DB設定
        self.db_config = db_config or {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', '5432')),
            'database': os.getenv('POSTGRES_DB', 'resonant_dashboard'),
            'user': os.getenv('POSTGRES_USER', 'resonant'),
            'password': os.getenv('POSTGRES_PASSWORD', '')
        }

    async def start(self):
        """Intent Bridge起動"""
        logger.info("🚀 Intent Bridge起動中...")

        # PostgreSQL接続プール作成
        self.pool = await asyncpg.create_pool(**self.db_config)
        logger.info("✅ PostgreSQL接続プール作成完了")

        self.running = True

        # LISTEN開始
        await self.listen_for_intents()

    async def listen_for_intents(self):
        """PostgreSQL LISTEN/NOTIFYでIntent検知"""
        async with self.pool.acquire() as conn:
            await conn.add_listener('intent_created', self.handle_notification)
            logger.info("🎧 LISTEN intent_created: 待機中...")

            # 無限ループ（キープアライブ）
            while self.running:
                await asyncio.sleep(1)

    async def handle_notification(self, conn, pid, channel, payload):
        """
        Intent作成通知を受信時のハンドラー

        Args:
            payload: JSON形式 {"id": "intent_id", "description": "...", "priority": ...}
        """
        try:
            data = json.loads(payload)
            intent_id = data.get('id')

            logger.info(f"📨 Intent受信: {intent_id}")

            # 非同期タスクとして処理開始（ブロッキング回避）
            asyncio.create_task(self.process_intent(intent_id))

        except Exception as e:
            logger.error(f"❌ 通知処理エラー: {e}")

    async def process_intent(self, intent_id: str):
        """
        Intent処理のメインロジック
        Sprint 4 + 4.5統合版
        """
        async with self.pool.acquire() as conn:
            try:
                # 1. Intent取得
                intent = await conn.fetchrow(
                    "SELECT * FROM intents WHERE id = $1",
                    uuid.UUID(intent_id)
                )

                if not intent:
                    logger.error(f"❌ Intent not found: {intent_id}")
                    return

                description = intent['description']

                # 2. Intent分類（Sprint 4.5）
                intent_type = self.classifier.classify(description)
                confidence = self.classifier.get_confidence(description)

                logger.info(f"📊 Intent分類: {intent_type} (信頼度: {confidence:.2f})")

                # 3. ステータス更新: processing
                await conn.execute(
                    """UPDATE intents
                       SET status = 'processing',
                           metadata = jsonb_set(
                               COALESCE(metadata, '{}'),
                               '{intent_type}',
                               to_jsonb($2::text)
                           ),
                           updated_at = NOW()
                       WHERE id = $1""",
                    uuid.UUID(intent_id),
                    intent_type
                )

                # 4. タイプに応じた処理
                if intent_type == 'code_execution':
                    result = await self._process_with_claude_code(conn, intent)
                else:
                    result = await self._process_with_claude_api(intent)

                # 5. 結果保存
                await conn.execute("""
                    UPDATE intents
                    SET status = 'completed',
                        result = $1,
                        processed_at = NOW(),
                        updated_at = NOW()
                    WHERE id = $2
                """, json.dumps(result), uuid.UUID(intent_id))

                # 6. 通知生成
                await self.create_notification(conn, intent_id, "success", result)

                logger.info(f"✅ Intent処理完了: {intent_id} ({intent_type})")

            except Exception as e:
                logger.error(f"❌ Intent処理失敗: {intent_id}: {e}")

                # エラー時の処理
                await conn.execute("""
                    UPDATE intents
                    SET status = 'failed',
                        result = $1,
                        updated_at = NOW()
                    WHERE id = $2
                """, json.dumps({"error": str(e)}), uuid.UUID(intent_id))

                await self.create_notification(conn, intent_id, "error", {"error": str(e)})

    async def _process_with_claude_code(self, conn, intent) -> Dict[str, Any]:
        """
        Claude Codeで処理（Sprint 4.5）
        Repository Mode + Context Auto-loading + DB Memory統合
        """
        intent_id = str(intent['id'])
        description = intent['description']

        logger.info(f"🤖 Claude Code実行: {intent_id}")

        # 1. コンテキスト自動ロード
        context = self.context_loader.load_context_for_intent(description, max_files=15)

        logger.info(f"📚 コンテキストロード完了:")
        logger.info(f"  - ファイル: {len(context['files'])}個")
        logger.info(f"  - 関連Sprint: {context['related_sprints']}")

        # 2. DB記憶統合（過去のIntent結果）
        db_memories = await self._fetch_relevant_memories(conn, intent)
        context['db_memories'] = db_memories

        logger.info(f"  - DB記憶: {len(db_memories)}件")

        # 3. Claude Codeセッション作成
        session_id = str(uuid.uuid4())
        session_record = await conn.fetchrow("""
            INSERT INTO claude_code_sessions
            (intent_id, session_id, status, workspace_mode, metadata)
            VALUES ($1, $2, 'running', $3, $4)
            RETURNING *
        """,
            intent['id'],
            session_id,
            'repository',
            json.dumps({
                'context_files': [str(f) for f in context['files']],
                'related_sprints': context['related_sprints']
            })
        )

        try:
            # 4. Claude Code実行
            code_result = await self.claude_code.execute_task(
                task_description=description,
                context=context,
                timeout=300
            )

            # 5. 実行履歴保存
            for idx, execution in enumerate(code_result.get('executions', [])):
                await conn.execute("""
                    INSERT INTO claude_code_executions
                    (session_id, execution_order, tool_name, input_data, output_data, success)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """,
                    session_record['id'],
                    idx,
                    execution.get('tool'),
                    json.dumps(execution.get('input', {})),
                    json.dumps(execution.get('output', {})),
                    execution.get('success', True)
                )

            # 6. セッション完了
            duration = (datetime.now() - session_record['started_at']).total_seconds()
            await conn.execute("""
                UPDATE claude_code_sessions
                SET status = 'completed',
                    completed_at = NOW(),
                    total_duration_seconds = $1,
                    metadata = jsonb_set(
                        metadata,
                        '{branch}',
                        to_jsonb($2::text)
                    )
                WHERE id = $3
            """, int(duration), code_result.get('branch', ''), session_record['id'])

            logger.info(f"✅ Claude Code実行完了: {duration:.1f}秒")

            return {
                'type': 'code_execution',
                'session_id': session_id,
                'output': code_result['output'],
                'file_changes': code_result.get('file_changes', []),
                'context_files_used': code_result.get('context_files_used', []),
                'branch': code_result.get('branch'),
                'success': code_result['success'],
                'duration_seconds': int(duration)
            }

        except asyncio.TimeoutError:
            await conn.execute(
                "UPDATE claude_code_sessions SET status = 'timeout' WHERE id = $1",
                session_record['id']
            )
            raise

        except Exception as e:
            await conn.execute(
                "UPDATE claude_code_sessions SET status = 'failed' WHERE id = $1",
                session_record['id']
            )
            raise

    async def _process_with_claude_api(self, intent) -> Dict[str, Any]:
        """
        Claude APIで処理（Sprint 4既存実装）
        質問応答、提案等
        """
        logger.info(f"💬 Claude API実行: {intent['id']}")

        message = self.claude_api.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": intent['description']
            }]
        )

        return {
            'type': 'chat',
            'response': message.content[0].text,
            'model': message.model,
            'tokens': message.usage.output_tokens
        }

    async def _fetch_relevant_memories(
        self,
        conn,
        intent,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        過去の類似Intent処理結果を取得（DB記憶）
        Sprint 4.5 Enhanced機能
        """
        description = intent['description']

        # 簡易キーワード抽出（改善の余地あり）
        keywords = description.split()[:5]

        # 類似Intent検索
        query = """
            SELECT id, description, status, result, processed_at
            FROM intents
            WHERE status = 'completed'
              AND id != $1
              AND (
                  description ILIKE ANY($2)
              )
            ORDER BY processed_at DESC
            LIMIT $3
        """

        search_patterns = [f"%{kw}%" for kw in keywords if len(kw) > 2]

        if not search_patterns:
            return []

        memories = await conn.fetch(query, intent['id'], search_patterns, limit)

        return [
            {
                'id': str(m['id']),
                'description': m['description'],
                'status': m['status'],
                'result': m['result'],
                'processed_at': m['processed_at'].isoformat() if m['processed_at'] else None
            }
            for m in memories
        ]

    async def create_notification(
        self,
        conn,
        intent_id: str,
        status: str,
        result: Optional[Dict[str, Any]] = None
    ):
        """通知生成"""
        title = "Intent処理完了" if status == "success" else "Intent処理失敗"
        notification_type = "success" if status == "success" else "error"

        # メッセージ生成
        if status == "success" and result:
            if result.get('type') == 'code_execution':
                message = f"Intent ID: {intent_id}\nClaude Code実行完了\nBranch: {result.get('branch', 'N/A')}"
            else:
                message = f"Intent ID: {intent_id}\nClaude API応答完了"
        else:
            error_msg = result.get('error', '不明なエラー') if result else '不明なエラー'
            message = f"Intent ID: {intent_id}\nエラー: {error_msg}"

        await conn.execute("""
            INSERT INTO notifications (user_id, title, message, notification_type)
            VALUES ('hiroki', $1, $2, $3)
        """, title, message, notification_type)

        logger.info(f"📬 通知生成: {title}")

    async def stop(self):
        """Intent Bridge停止"""
        logger.info("🛑 Intent Bridge停止中...")
        self.running = False

        if self.pool:
            await self.pool.close()

        logger.info("✅ Intent Bridge停止完了")


# エントリーポイント
async def main():
    """Intent Bridge起動"""
    bridge = IntentBridge()

    try:
        await bridge.start()
    except KeyboardInterrupt:
        logger.info("\n🛑 KeyboardInterrupt: 停止シグナル受信")
        await bridge.stop()
    except Exception as e:
        logger.error(f"❌ Intent Bridge エラー: {e}")
        await bridge.stop()


if __name__ == '__main__':
    asyncio.run(main())
