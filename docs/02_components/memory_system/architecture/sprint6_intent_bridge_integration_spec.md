# Sprint 6: Intent Bridge - Context Assembler統合仕様書

## 1. 概要

### 1.1 目的
Intent BridgeにContext Assemblerを統合し、Claude APIとの対話に過去の会話履歴と関連する長期記憶を自動的に含めることで、文脈を維持した高品質な応答を実現する。

### 1.2 背景
**現状の問題:**
- Intent Bridgeは毎回単一メッセージのみをClaude APIに送信
- Claudeは過去の会話を記憶せず、毎回ゼロリセット状態
- PostgreSQLに保存された会話履歴（1,500+件）と長期記憶（3,800+件）が活用されていない
- ユーザーは毎回前提を説明し直す必要がある

**Sprint 5での成果:**
- Context Assembler実装完了（3層記憶統合）
- KanaAIBridge統合完了（Context Assembler対応）
- 99%のデータ削減率を実現（1,100+件 → 7メッセージ）

**残課題:**
Intent BridgeがKanaAIBridgeを使用していないため、Context Assemblerが活用されていない。

### 1.3 目標
- Intent BridgeからKanaAIBridge経由でContext Assemblerを使用
- PostgreSQLデータの活用率を0% → 95%に向上
- ユーザーの説明負担を80%削減
- Intent処理精度を60% → 90%に向上

---

## 2. アーキテクチャ

### 2.1 現状アーキテクチャ（問題あり）

```
Intent Bridge (intent_bridge/processor.py)
  |
  ├─ anthropic.Anthropic (直接インスタンス化) ❌
  |   └─ messages.create([単一メッセージ]) ❌
  |
  └─ PostgreSQL (intents, notifications のみ使用)
      └─ messages, memories テーブルは死蔵 ❌

分離された実装（使われていない）:
  - KanaAIBridge (Context Assembler統合済み) ✅
  - Context Assembler (3層記憶統合) ✅
  - Memory Store (PostgreSQL活用) ✅
  - Retrieval Orchestrator (ベクトル検索) ✅
```

### 2.2 統合後アーキテクチャ（正しい形）

```
Intent Bridge
  |
  ├─ BridgeFactory ← NEW
  |   └─ create_ai_bridge_with_memory() ← NEW
  |       |
  |       ├─ ContextAssemblerFactory ← NEW
  |       |   └─ create_context_assembler()
  |       |       ├─ MessageRepository (Working Memory)
  |       |       ├─ MemoryRepository (Semantic Memory)
  |       |       └─ RetrievalOrchestrator (Vector Search)
  |       |
  |       └─ KanaAIBridge(context_assembler=...) ✅
  |           └─ process_intent()
  |               ├─ Context Assembler
  |               |   ├─ Working Memory: 直近10件
  |               |   ├─ Semantic Memory: 関連5件（ベクトル検索）
  |               |   └─ Session Summary: セッション要約
  |               |
  |               └─ Claude API (文脈付きメッセージリスト)
  |
  └─ PostgreSQL (全テーブル活用) ✅
      ├─ intents (Intent管理)
      ├─ messages (Working Memory)
      ├─ memories (Semantic Memory)
      └─ notifications (通知)
```

### 2.3 データフロー

```
[Intent作成]
  ↓
Intent Bridge.process(intent_id)
  ↓
1. PostgreSQLからIntent取得
  ↓
2. BridgeFactory.create_ai_bridge_with_memory()
   ├─ ContextAssemblerFactory初期化
   |   ├─ DB接続プール取得
   |   ├─ MessageRepository初期化
   |   ├─ MemoryRepository初期化
   |   └─ RetrievalOrchestrator初期化
   |
   └─ KanaAIBridge初期化(context_assembler=...)
  ↓
3. KanaAIBridge.process_intent({
     content: intent.description,
     user_id: intent.user_id,
     session_id: intent.session_id
   })
   ↓
   3-1. Context Assembler.assemble_context()
        ├─ Working Memory取得（直近10件）
        ├─ Semantic Memory検索（関連5件）
        └─ メッセージリスト構築
   ↓
   3-2. Claude API呼び出し（文脈付き）
   ↓
   3-3. 応答 + context_metadata返却
  ↓
4. 結果をPostgreSQLに保存
   ├─ intents.result ← Claude応答
   └─ intents.metadata ← context_metadata (NEW)
  ↓
5. 通知作成
```

---

## 3. コンポーネント設計

### 3.1 Context Assembler Factory

**ファイル:** `context_assembler/factory.py`

**責務:**
- Context Assemblerインスタンスの生成
- 依存関係（MessageRepository, MemoryRepository, RetrievalOrchestrator）の初期化
- データベース接続プールの管理

**インターフェース:**

```python
async def create_context_assembler(
    pool: Optional[asyncpg.Pool] = None,
    config: Optional[ContextConfig] = None,
) -> ContextAssemblerService:
    """
    Context Assemblerインスタンスを生成

    Args:
        pool: PostgreSQL接続プール（Noneの場合は新規作成）
        config: Context設定（Noneの場合はデフォルト）

    Returns:
        ContextAssemblerService: 初期化済みインスタンス

    Raises:
        ConnectionError: データベース接続失敗
        ValueError: 依存関係の初期化失敗
    """
```

**実装詳細:**

```python
# context_assembler/factory.py

import asyncpg
from typing import Optional
from context_assembler.service import ContextAssemblerService
from context_assembler.config import get_default_config, ContextConfig
from memory_store.repository import MessageRepository, MemoryRepository
from retrieval.orchestrator import RetrievalOrchestrator
from config.database import get_database_url

async def create_context_assembler(
    pool: Optional[asyncpg.Pool] = None,
    config: Optional[ContextConfig] = None,
) -> ContextAssemblerService:
    """Context Assemblerインスタンスを生成"""

    # 1. データベース接続プール
    if pool is None:
        database_url = get_database_url()
        pool = await asyncpg.create_pool(database_url, min_size=2, max_size=10)

    # 2. リポジトリ初期化
    message_repo = MessageRepository(pool)
    memory_repo = MemoryRepository(pool)

    # 3. Retrieval Orchestrator初期化
    retrieval = RetrievalOrchestrator(
        memory_repo=memory_repo,
        # 他の依存関係...
    )

    # 4. Context Assembler初期化
    return ContextAssemblerService(
        message_repo=message_repo,
        retrieval=retrieval,
        config=config or get_default_config(),
    )
```

### 3.2 BridgeFactory拡張

**ファイル:** `bridge/factory/bridge_factory.py`

**変更内容:**
1. `create_ai_bridge_with_memory()` メソッド追加（非同期）
2. 既存の `create_ai_bridge()` は後方互換性のため保持

**新規メソッド:**

```python
@staticmethod
async def create_ai_bridge_with_memory(
    bridge_type: Optional[str] = None,
    pool: Optional[asyncpg.Pool] = None,
) -> AIBridge:
    """
    Context Assembler統合版のAI Bridgeを生成

    Args:
        bridge_type: "kana", "claude", "mock"（デフォルト: 環境変数）
        pool: PostgreSQL接続プール（Noneの場合は新規作成）

    Returns:
        AIBridge: Context Assembler統合済みのAI Bridge

    Raises:
        ValueError: 未対応のbridge_type
        ConnectionError: Context Assembler初期化失敗
    """
    from context_assembler.factory import create_context_assembler

    bridge_key = (bridge_type or os.getenv("AI_BRIDGE_TYPE", "kana")).lower()

    if bridge_key in {"kana", "claude"}:
        # Context Assembler初期化
        context_assembler = await create_context_assembler(pool=pool)
        return KanaAIBridge(context_assembler=context_assembler)

    if bridge_key == "mock":
        # Mockは従来通り
        return MockAIBridge()

    raise ValueError(f"Unsupported AI_BRIDGE_TYPE: {bridge_key}")
```

### 3.3 Intent Bridge修正

**ファイル:** `intent_bridge/intent_bridge/processor.py`

**変更内容:**
1. `__init__()`: Claude直接インスタンス化を削除、ai_bridge属性追加
2. `initialize()`: BridgeFactory経由でKanaAIBridge初期化（非同期）
3. `call_claude()`: KanaAIBridge.process_intent()を使用
4. `process()`: 初期化ロジック追加

**変更後の実装:**

```python
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
        """通知作成（変更なし）"""
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
```

---

## 4. データモデル

### 4.1 Intent結果の拡張

**テーブル:** `intents`

**変更:** `result` カラムのJSONB構造に `context_metadata` フィールド追加

**従来の構造:**
```json
{
  "response": "...",
  "model": "claude-sonnet-4-20250514",
  "usage": {
    "input_tokens": 150,
    "output_tokens": 200
  },
  "processed_at": "2025-11-18T10:00:00Z"
}
```

**新構造:**
```json
{
  "response": "...",
  "model": "claude-sonnet-4-20250514",
  "usage": {
    "input_tokens": 150,
    "output_tokens": 200
  },
  "context_metadata": {
    "working_memory_count": 10,
    "semantic_memory_count": 5,
    "has_session_summary": false,
    "total_tokens": 3240,
    "compression_applied": false
  },
  "processed_at": "2025-11-18T10:00:00Z"
}
```

---

## 5. 設定・環境変数

### 5.1 必須環境変数

```bash
# Claude API
ANTHROPIC_API_KEY=sk-ant-...

# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/resonant_engine

# Bridge Type
AI_BRIDGE_TYPE=kana  # "kana" または "claude"（Context Assembler統合）
                      # "mock"（テスト用）
```

### 5.2 オプション設定

Context Assemblerの設定は `context_assembler/config.py` で管理：

```python
ContextConfig(
    system_prompt="You are Kana, the external translator for Resonant Engine.",
    working_memory_limit=10,      # Working Memory取得件数
    semantic_memory_limit=5,      # Semantic Memory取得件数
    max_tokens=100000,            # Claude API上限
    token_safety_margin=0.8,      # 安全マージン（80%）
)
```

---

## 6. エラーハンドリング

### 6.1 初期化失敗時

```python
# BridgeFactory初期化失敗
try:
    ai_bridge = await BridgeFactory.create_ai_bridge_with_memory()
except ConnectionError as e:
    logger.error(f"Database connection failed: {e}")
    # Fallback: Mockモード or リトライ

except ValueError as e:
    logger.error(f"Configuration error: {e}")
    # Fallback: デフォルト設定 or 終了
```

### 6.2 Context組み立て失敗時

KanaAIBridge内で自動的にFallback（Sprint 5で実装済み）：

```python
# KanaAIBridge.process_intent()
if self._context_assembler and user_message:
    try:
        assembled = await self._context_assembler.assemble_context(...)
        messages = assembled.messages
    except Exception as e:
        warnings.warn(f"Context assembly failed: {e}, falling back to simple mode")
        messages = self._build_simple_messages(intent)  # Fallback
```

### 6.3 Claude API失敗時

```python
# Intent Bridge.call_claude()
try:
    result = await self.ai_bridge.process_intent(...)
except APIStatusError as e:
    logger.error(f"Claude API error: {e}")
    # Intents.status = 'failed'
    # Notification作成
```

---

## 7. パフォーマンス考慮事項

### 7.1 データベース接続プール

```python
# Factory初期化時
pool = await asyncpg.create_pool(
    database_url,
    min_size=2,     # 最小接続数
    max_size=10,    # 最大接続数（Intent処理の並行度に応じて調整）
    timeout=30,     # 接続タイムアウト
)
```

### 7.2 Context Assembler並行取得

Context Assemblerは3層を並行取得（Sprint 5実装済み）：

```python
# context_assembler/service.py
memory_layers = await asyncio.gather(
    self._fetch_working_memory(...),   # 並行
    self._fetch_semantic_memory(...),  # 並行
    self._fetch_session_summary(...),  # 並行
)
```

### 7.3 キャッシング戦略

**Phase 1（このSprint）:** キャッシュなし（シンプル実装）

**Phase 2（将来）:**
- Session Summary のキャッシュ（セッション単位）
- Semantic Memory のTTL付きキャッシュ

---

## 8. セキュリティ考慮事項

### 8.1 データベース認証情報

```python
# 環境変数から取得（ハードコード禁止）
database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise ValueError("DATABASE_URL must be set")
```

### 8.2 SQLインジェクション対策

```python
# パラメータ化クエリを使用（asyncpg）
await conn.execute(
    "SELECT * FROM intents WHERE id = $1",  # ✅ $1プレースホルダ
    intent_id
)
# NG: f"SELECT * FROM intents WHERE id = '{intent_id}'"
```

### 8.3 APIキー管理

```python
# KanaAIBridge初期化時
api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    raise ValueError("ANTHROPIC_API_KEY must be set")
```

---

## 9. Done Definition（完了条件）

### Tier 1: 必須（Must Have）

- [ ] Context Assembler Factory実装完了
  - `create_context_assembler()` 関数
  - 依存関係の正しい初期化
  - エラーハンドリング

- [ ] BridgeFactory拡張完了
  - `create_ai_bridge_with_memory()` メソッド
  - 後方互換性維持（既存の `create_ai_bridge()` 保持）
  - 環境変数サポート

- [ ] Intent Bridge修正完了
  - `initialize()` メソッド追加
  - `call_claude()` のKanaAIBridge化
  - `process()` の初期化ロジック
  - context_metadata保存

- [ ] 単体テスト実装
  - Context Assembler Factoryテスト（5件）
  - BridgeFactoryテスト（3件）
  - Intent Bridgeテスト（8件）

- [ ] E2Eテスト実装
  - Intent作成 → 処理 → 結果確認（文脈あり）
  - Context metadata検証
  - Fallback動作確認

- [ ] 受け入れテスト全件PASS
  - 14テストケース全て成功

### Tier 2: 推奨（Should Have）

- [ ] ログ出力の充実
  - Context metadata のログ出力
  - 処理時間計測
  - エラー詳細ログ

- [ ] ドキュメント更新
  - README更新（統合手順）
  - 環境変数一覧更新

- [ ] パフォーマンス測定
  - 統合前後の処理時間比較
  - Context組み立て時間計測

---

## 10. スコープ外（Out of Scope）

このSprintでは以下を実装**しない**：

- ❌ Session Summary自動生成（Sprint 7予定）
- ❌ Context Assemblerのキャッシング
- ❌ ユーザー別設定（working_memory_limit等）
- ❌ Dashboard UIの更新
- ❌ Intent Bridge以外のコンポーネント統合

---

## 11. リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| 依存関係（Memory Store, Retrieval）が未実装 | 高 | 実装確認、Mock使用 |
| データベース接続プール枯渇 | 中 | プールサイズ調整、タイムアウト設定 |
| Context組み立て失敗 | 低 | Fallback実装済み（Sprint 5） |
| 既存Intent処理への影響 | 中 | 後方互換性確保、段階的移行 |

---

## 12. 依存関係

### 必須（このSprintで必要）
- ✅ Context Assembler（Sprint 5実装済み）
- ✅ KanaAIBridge（Sprint 5実装済み）
- ⚠️ Memory Store（確認必要）
- ⚠️ Retrieval Orchestrator（確認必要）

### 確認コマンド
```bash
# Memory Store実装確認
ls -la memory_store/repository.py

# Retrieval Orchestrator実装確認
ls -la retrieval/orchestrator.py

# PostgreSQLテーブル確認
psql -U postgres -d resonant_engine -c "\dt"
```

---

## 13. 実装スケジュール

### Day 1: Factory層実装
- Context Assembler Factory実装
- BridgeFactory拡張
- 単体テスト（Factory層）

### Day 2: Intent Bridge修正
- processor.py修正
- 単体テスト（Intent Bridge）

### Day 3: 統合テスト
- E2Eテスト実装
- 受け入れテスト実行

### Day 4: レビューと修正
- コードレビュー
- バグ修正
- ドキュメント更新

---

## 14. 成功指標（Success Metrics）

### 定量指標
- ✅ 受け入れテスト成功率: 100%（14/14）
- ✅ PostgreSQLデータ活用率: 95%以上（Working Memory + Semantic Memory）
- ✅ Context組み立て成功率: 95%以上
- ✅ 応答時間: 平均3秒以内（Context組み立て + Claude API）

### 定性指標
- ✅ Claudeが過去の会話を参照して応答
- ✅ ユーザーが前提を説明し直す必要がない
- ✅ コードの可読性・保守性が向上
- ✅ アーキテクチャの整合性確保

---

## 15. 参考資料

- [Sprint 5: Context Assembler仕様書](./sprint5_context_assembler_spec.md)
- [KanaAIBridge実装](../../bridge/providers/ai/kana_ai_bridge.py)
- [Intent Bridge現在の実装](../../../intent_bridge/intent_bridge/processor.py)
- [Context Assemblerデモ](../../../examples/context_assembler_demo.py)
