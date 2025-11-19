import json
import logging
import uuid
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class IntentProcessor:
    def __init__(self, pool, config):
        self.pool = pool
        self.config = config
        self.ai_bridge = None  # KanaAIBridge（Context Assembler統合）
        self.claude_code_client = None  # Claude Code Client
        self.classifier = None  # Intent Classifier
        self.session_manager = None  # Sprint 7: Session Manager

    async def initialize(self):
        """非同期初期化: KanaAIBridge、Claude Code Client、Classifierを生成"""
        from bridge.factory.bridge_factory import BridgeFactory
        from .claude_code_client import ClaudeCodeClient
        from .classifier import IntentClassifier

        try:
            # KanaAIBridge（Context Assembler統合）初期化
            self.ai_bridge = await BridgeFactory.create_ai_bridge_with_memory(
                bridge_type="kana",
                pool=self.pool,
            )
            logger.info("✅ KanaAIBridge initialized with Context Assembler")

            # Claude Code Client初期化
            self.claude_code_client = ClaudeCodeClient()
            logger.info("✅ Claude Code Client initialized")

            # Intent Classifier初期化
            self.classifier = IntentClassifier()
            logger.info("✅ Intent Classifier initialized")

            # Sprint 7: SessionManager初期化
            await self._initialize_session_manager()

        except Exception as e:
            logger.error(f"❌ Failed to initialize IntentProcessor components: {e}")
            raise

    async def _initialize_session_manager(self):
        """Sprint 7: SessionManagerを初期化"""
        try:
            from memory_store.session_summary_repository import SessionSummaryRepository
            from summarization.service import SummarizationService
            from session.manager import SessionManager

            summary_repo = SessionSummaryRepository(self.pool)
            summarization_service = SummarizationService(summary_repo=summary_repo)
            self.session_manager = SessionManager(
                summary_repo=summary_repo,
                summarization_service=summarization_service,
            )
            logger.info("✅ SessionManager initialized")
        except Exception as e:
            logger.warning(f"⚠️ SessionManager initialization failed: {e}")
            self.session_manager = None

    async def process(self, intent_id):
        # 初回呼び出し時のみ初期化
        if self.ai_bridge is None:
            await self.initialize()

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
                    # KanaAIBridge経由でClaude API処理（Context Assembler統合）
                    logger.info(f"💬 Processing with KanaAIBridge (Context Assembler)...")
                    response = await self.call_claude(
                        description=intent['description'],
                        user_id=intent.get('user_id', 'hiroki'),
                        session_id=intent.get('session_id'),
                    )

                # 5. 結果保存
                # response構造を統一: message-response形式に変換
                if intent_type == 'code_execution':
                    result_data = response  # 既に完全な形式
                else:
                    # KanaAIBridge応答を統一形式に変換
                    result_data = {
                        "type": "chat",
                        "response": response["response"],
                        "model": response["model"],
                        "usage": response.get("usage", {}),
                        "context_metadata": response.get("context_metadata"),  # Context Assembler metadata
                        "processed_at": response["processed_at"],
                    }

                await conn.execute("""
                    UPDATE intents
                    SET status = 'completed',
                        result = $1::jsonb,
                        processed_at = NOW(),
                        updated_at = NOW()
                    WHERE id = $2
                """, json.dumps(result_data), intent_id)

                # 6. 通知作成
                await self.create_notification(conn, intent_id, 'success', intent_type)

                logger.info(f"✅ Intent {intent_id} processed successfully ({intent_type})")
                if intent_type == 'chat' and response.get("context_metadata"):
                    logger.info(
                        f"📊 Context: WM={response['context_metadata']['working_memory_count']}, "
                        f"SM={response['context_metadata']['semantic_memory_count']}"
                    )

                # Sprint 7: Session Summary自動生成チェック
                await self._check_session_summary(
                    conn=conn,
                    user_id=intent.get('user_id', 'hiroki'),
                    session_id=intent.get('session_id'),
                )

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

    async def call_claude(
        self,
        description: str,
        user_id: str = "hiroki",
        session_id: Optional[str] = None,
    ):
        """
        KanaAIBridge経由でClaude APIを呼び出し（Context Assembler統合）

        Args:
            description: Intent内容
            user_id: ユーザーID
            session_id: セッションID（オプション）

        Returns:
            dict: {
                "response": str,
                "model": str,
                "usage": dict,
                "context_metadata": dict,  # Context Assemblerメタデータ
                "processed_at": str,
            }
        """
        if self.ai_bridge:
            try:
                # KanaAIBridge.process_intent()を呼び出し
                result = await self.ai_bridge.process_intent({
                    "content": description,
                    "user_id": user_id,
                    "session_id": session_id,
                })

                # レスポンス整形
                return {
                    "response": result.get("summary", ""),
                    "model": result.get("model", "unknown"),
                    "usage": result.get("usage", {}),
                    "context_metadata": result.get("context_metadata"),
                    "processed_at": datetime.utcnow().isoformat(),
                }

            except Exception as e:
                logger.error(f"KanaAIBridge error: {e}")
                raise

        # Fallback: Mock応答（ai_bridgeが初期化失敗した場合のみ）
        logger.warning("⚠️ Using mock response (KanaAIBridge not initialized)")
        return {
            "response": f"[Mock Response] Intent processed: {description[:100]}",
            "model": "mock",
            "usage": {"input_tokens": 0, "output_tokens": 0},
            "context_metadata": None,
            "processed_at": datetime.utcnow().isoformat(),
        }

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

    async def _check_session_summary(
        self,
        conn,
        user_id: str,
        session_id: Optional[str],
    ) -> None:
        """Sprint 7: Session Summary生成チェック"""
        if not session_id or not self.session_manager:
            return

        try:
            # メッセージを取得（直近100件）
            messages_rows = await conn.fetch("""
                SELECT content, message_type as role, created_at
                FROM messages
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT 100
            """, user_id)

            if not messages_rows:
                return

            # メッセージを辞書形式に変換（新しい順→古い順に変換）
            messages = [
                {
                    'role': row['role'],
                    'content': row['content'],
                    'created_at': row['created_at'],
                }
                for row in reversed(messages_rows)  # 古い順に変換
            ]

            # 要約生成チェック
            from uuid import UUID
            summary = await self.session_manager.check_and_create_summary(
                user_id=user_id,
                session_id=UUID(session_id),
                messages=messages,
            )

            if summary:
                logger.info(
                    f"📝 Session Summary created for session {session_id}: "
                    f"{summary.summary[:80]}..."
                )
        except Exception as e:
            logger.warning(f"⚠️ Failed to check session summary: {e}")
            # エラーでも処理は継続（非クリティカル）

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
