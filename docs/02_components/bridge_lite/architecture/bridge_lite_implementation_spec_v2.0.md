# Bridge Lite Implementation Specification v2.0
_Concrete APIs, Data Schemas, and Integration Details_

この文書は **Bridge Lite Architecture Specification v2.0** を前提とし、
実装レイヤで必要となる API・クラス・DB スキーマ・テスト仕様を定義します。

---

## 1. モジュール構成（論理）

推奨ディレクトリ構成（例）:

```text
bridge/
  core/
    data_bridge.py
    ai_bridge.py
    feedback_bridge.py
    audit_logger.py
    factory.py
  providers/
    data/
      postgres_data_bridge.py
      mock_data_bridge.py
    ai/
      kana_ai_bridge.py
      mock_ai_bridge.py
    feedback/
      yuno_feedback_bridge.py
      mock_feedback_bridge.py
    audit/
      postgres_audit_logger.py
      mock_audit_logger.py
tests/
  bridge/
    test_mock_data_bridge.py
    test_postgresql_smoke.py
    test_audit_logger_smoke.py
daemon/
  observer_daemon.py
  resonant_daemon_db.py
docs/
  bridge_lite_architecture_spec_v2.0.md
  bridge_lite_implementation_spec_v2.0.md
```

---

## 2. 抽象インターフェース

### 2.1 DataBridge

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class DataBridge(ABC):
    @abstractmethod
    async def save_intent(self, intent_type: str, payload: Dict[str, Any]) -> str:
        """Intent を保存し intent_id を返す"""

    @abstractmethod
    async def get_intent(self, intent_id: str) -> Dict[str, Any]:
        """intent_id から Intent を取得"""

    @abstractmethod
    async def save_correction(self, intent_id: str, correction: Dict[str, Any]) -> None:
        """Correction Plan を保存"""

    @abstractmethod
    async def list_intents(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """状態でフィルタした Intent を列挙（必要に応じて拡張）"""
```

### 2.2 AIBridge

```python
class AIBridge(ABC):
    @abstractmethod
    async def process_intent(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """
        Intent を AI（主に Kana）に渡し、一次解析結果を返す。
        """
```

### 2.3 FeedbackBridge（Phase 1/2）

Phase 1 では既存の簡易フローのみ必須とし、
Phase 2 で Re-evaluation 関連メソッドを有効化します。

```python
class FeedbackBridge(ABC):
    # Phase 1: 必須（既存）
    @abstractmethod
    async def request_reevaluation(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """
        既存の簡易 Re-evaluation 要請。
        """

    # Phase 2: 拡張（Re-evaluation フル機能）
    @abstractmethod
    async def submit_feedback(self, intent_id: str, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """
        フィードバックを登録し、必要であれば一次応答を生成する。
        """

    @abstractmethod
    async def reanalyze(self, intent: Dict[str, Any], history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Intent + Feedback 歴史をもとに再評価結果を返す。
        """

    @abstractmethod
    async def generate_correction(
        self,
        intent: Dict[str, Any],
        feedback_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        再評価結果に基づき Correction Plan を生成する。
        """
```

### 2.4 AuditLogger

```python
class AuditLogger(ABC):
    @abstractmethod
    async def log(
        self,
        bridge_type: str,
        operation: str,
        details: Dict[str, Any],
        intent_id: Optional[str],
        correlation_id: Optional[str] = None,
        level: str = "INFO",
    ) -> None:
        """
        監査ログを記録する。
        bridge_type: 'data' / 'ai' / 'feedback' / 'daemon' など
        operation: 'save_intent' / 'process_intent' / ...
        """

    @abstractmethod
    async def cleanup(self) -> None:
        """ローテーション・削除処理を行う。"""
```

---

## 3. PostgreSQL スキーマ

### 3.1 intents テーブル

```sql
CREATE TABLE IF NOT EXISTS intents (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    type TEXT NOT NULL,
    payload JSONB NOT NULL,
    status TEXT NOT NULL,
    correlation_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 3.2 intent_corrections テーブル

```sql
CREATE TABLE IF NOT EXISTS intent_corrections (
    id SERIAL PRIMARY KEY,
    intent_id TEXT NOT NULL REFERENCES intents(id) ON DELETE CASCADE,
    correction JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 3.3 audit_logs テーブル

```sql
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    bridge_type TEXT NOT NULL,
    operation TEXT NOT NULL,
    level TEXT NOT NULL DEFAULT 'INFO',
    details JSONB,
    intent_id TEXT,
    correlation_id TEXT
);
```

---

## 4. PostgreSQL DataBridge 実装ポイント

- ライブラリ: asyncpg を想定
- 接続パラメータは環境変数または設定ファイルから取得

```python
import uuid
import asyncpg

class PostgresDataBridge(DataBridge):
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def save_intent(self, intent_type: str, payload: Dict[str, Any]) -> str:
        intent_id = str(uuid.uuid4())
        correlation_id = payload.get("correlation_id") or str(uuid.uuid4())
        await self._pool.execute(
            """
            INSERT INTO intents (id, source, type, payload, status, correlation_id)
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            intent_id,
            payload.get("source", "daemon"),
            intent_type,
            payload,
            "RECORDED",
            correlation_id,
        )
        return intent_id

    async def get_intent(self, intent_id: str) -> Dict[str, Any]:
        row = await self._pool.fetchrow(
            "SELECT id, source, type, payload, status, correlation_id FROM intents WHERE id = $1",
            intent_id,
        )
        if row is None:
            raise KeyError(f"intent not found: {intent_id}")
        return {
            "id": row["id"],
            "source": row["source"],
            "type": row["type"],
            "payload": row["payload"],
            "status": row["status"],
            "correlation_id": row["correlation_id"],
        }
```

---

## 5. PostgreSQL AuditLogger 実装ポイント

```python
class PostgresAuditLogger(AuditLogger):
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def log(
        self,
        bridge_type: str,
        operation: str,
        details: Dict[str, Any],
        intent_id: Optional[str],
        correlation_id: Optional[str] = None,
        level: str = "INFO",
    ) -> None:
        await self._pool.execute(
            """
            INSERT INTO audit_logs (bridge_type, operation, level, details, intent_id, correlation_id)
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            bridge_type,
            operation,
            level,
            details,
            intent_id,
            correlation_id,
        )

    async def cleanup(self) -> None:
        # 例: 30日より古いログを削除
        await self._pool.execute(
            "DELETE FROM audit_logs WHERE timestamp < now() - INTERVAL '30 days'"
        )
```

---

## 6. Daemon 統合仕様（実装観点）

### 6.1 BridgeFactory 利用

```python
from bridge.core.factory import BridgeFactory

data_bridge = BridgeFactory.create_data_bridge()
ai_bridge = BridgeFactory.create_ai_bridge()
feedback_bridge = BridgeFactory.create_feedback_bridge()
audit_logger = BridgeFactory.create_audit_logger()
```

### 6.2 Intent ハンドラの実装例

```python
async def handle_intent(intent: Dict[str, Any]) -> Dict[str, Any]:
    # 1. Intent 保存
    intent_id = await data_bridge.save_intent(intent["type"], intent)

    await audit_logger.log(
        bridge_type="data",
        operation="save_intent",
        details={"intent_type": intent["type"]},
        intent_id=intent_id,
        correlation_id=intent.get("correlation_id"),
    )

    # 2. AI 一次処理
    ai_result = await ai_bridge.process_intent(intent)

    await audit_logger.log(
        bridge_type="ai",
        operation="process_intent",
        details={"status": "ok"},
        intent_id=intent_id,
        correlation_id=intent.get("correlation_id"),
    )

    # 3. Phase 1: 簡易 Re-evaluation（request_reevaluation）
    reeval = await feedback_bridge.request_reevaluation(intent)

    await audit_logger.log(
        bridge_type="feedback",
        operation="request_reevaluation",
        details={"status": "ok"},
        intent_id=intent_id,
        correlation_id=intent.get("correlation_id"),
    )

    # Phase 2 以降で:
    # - submit_feedback
    # - reanalyze
    # - generate_correction
    # を順次呼び出して Correction Plan を保存する。

    return {
        "intent_id": intent_id,
        "ai_result": ai_result,
        "reeval": reeval,
    }
```

---

## 7. 環境変数と設定

### 7.1 Bridge の種類

```text
DATA_BRIDGE_TYPE=postgresql | mock
AI_BRIDGE_TYPE=kana | mock
FEEDBACK_BRIDGE_TYPE=yuno | mock
AUDIT_LOGGER_TYPE=postgresql | mock
```

### 7.2 DB 接続

```text
POSTGRES_DSN=postgresql://user:password@localhost:5432/resonant
```

---

## 8. スモークテスト仕様

### 8.1 PostgreSQL Bridge スモーク

```python
@pytest.mark.asyncio
async def test_postgresql_bridge_smoke():
    bridge = BridgeFactory.create_data_bridge(type="postgresql")
    async with bridge:
        intent_id = await bridge.save_intent("test", {"msg": "hello"})
        result = await bridge.get_intent(intent_id)
    assert result["payload"]["msg"] == "hello"
```

### 8.2 AuditLogger スモーク

```python
@pytest.mark.asyncio
async def test_audit_logger_smoke():
    logger = BridgeFactory.create_audit_logger(type="postgresql")
    await logger.log(
        bridge_type="test",
        operation="smoke_test",
        details={"ok": True},
        intent_id=None,
    )
    # SELECT で1件以上返ることを確認する簡易チェックを追加してもよい
```

---

## 9. フェーズ別の実装境界

- Phase 0.5
  - DataBridge(PostgreSQL) 最低限実装
  - AuditLogger(PostgreSQL) 実装
  - 上記のスモークテストを CI に組み込み

- Phase 1
  - Daemon → Bridge Lite 統合
  - request_reevaluation ベースの簡易 Re-evaluation を動かす

- Phase 2
  - FeedbackBridge の 3 メソッド（submit_feedback / reanalyze / generate_correction）本実装
  - Correction Plan の保存・参照ラインを拡張

- Phase 3
  - Memory / Semantic Bridge との統合は別仕様で定義
