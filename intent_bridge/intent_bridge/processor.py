import json
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class IntentProcessor:
    def __init__(self, pool, config):
        self.pool = pool
        self.config = config
        self.ai_bridge = None  # KanaAIBridgeを格納

    async def initialize(self):
        """非同期初期化: KanaAIBridge（Context Assembler統合）を生成"""
        from bridge.factory.bridge_factory import BridgeFactory

        try:
            self.ai_bridge = await BridgeFactory.create_ai_bridge_with_memory(
                bridge_type="kana",
                pool=self.pool,
            )
            logger.info("✅ KanaAIBridge initialized with Context Assembler")
        except Exception as e:
            logger.error(f"❌ Failed to initialize KanaAIBridge: {e}")
            raise

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

            # 2. ステータス更新: processing
            await conn.execute("""
                UPDATE intents
                SET status = 'processing', updated_at = NOW()
                WHERE id = $1
            """, intent_id)

            try:
                # 3. KanaAIBridge経由でClaude API呼び出し
                logger.info(f"🤖 Processing intent via KanaAIBridge...")
                response = await self.call_claude(
                    description=intent['description'],
                    user_id=intent.get('user_id', 'hiroki'),
                    session_id=intent.get('session_id'),
                )

                # 4. 結果保存（metadata含む）
                result_data = {
                    "response": response["response"],
                    "model": response["model"],
                    "usage": response.get("usage", {}),
                    "context_metadata": response.get("context_metadata"),  # NEW
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

                # 5. 通知作成
                await self.create_notification(conn, intent_id, 'success')

                logger.info(f"✅ Intent {intent_id} processed successfully")
                if response.get("context_metadata"):
                    logger.info(
                        f"📊 Context: WM={response['context_metadata']['working_memory_count']}, "
                        f"SM={response['context_metadata']['semantic_memory_count']}"
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

                await self.create_notification(conn, intent_id, 'error')
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
