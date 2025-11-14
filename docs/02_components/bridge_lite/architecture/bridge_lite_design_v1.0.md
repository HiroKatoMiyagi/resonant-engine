# 🌉 Bridge Lite - 基本設計書

**バージョン**: 1.0.0  
**作成日**: 2025年11月12日  
**ステータス**: 設計フェーズ

---

## 📋 目次

1. [概要](#概要)
2. [設計原則](#設計原則)
3. [アーキテクチャ](#アーキテクチャ)
4. [コンポーネント設計](#コンポーネント設計)
5. [実装仕様](#実装仕様)
6. [移行計画](#移行計画)
7. [テスト戦略](#テスト戦略)

---

## 📖 概要

### 目的

Bridge Liteは、Resonant Engineにおける**データアクセス層とAI API層を抽象化する軽量な中間層**です。

### 解決する問題

**現状の課題**:
1. PostgreSQL直接依存が強すぎる（`asyncpg`直接呼び出し）
2. AI API（Claude）への直接依存
3. ログが各所に散在
4. テスト困難（実DB必須）
5. 将来の拡張（GitHub/Slack統合）に対応できない

**Bridge Lite導入後**:
1. ✅ データベース抽象化（PostgreSQL/MySQL切り替え可能）
2. ✅ AI API抽象化（Claude/GPT-4切り替え可能）
3. ✅ 監査ログ一元化
4. ✅ テスト容易化（モックBridge使用）
5. ✅ 外部API統合基盤

### スコープ

**含むもの**:
- データアクセス抽象化（DataBridge）
- AI API抽象化（AIBridge）
- 監査ログ統合（AuditLogger）
- Intent Protocol定義
- 設定管理

**含まないもの（将来実装）**:
- 非同期キュー（Async Queue）
- 外部API統合（GitHub/Slack）
- Webhookレシーバー
- レート制限管理

---

## 🎯 設計原則

### 1. SOLID原則の適用

```python
# Single Responsibility Principle（単一責任の原則）
# - DataBridgeはデータアクセスのみ
# - AIBridgeはAI API呼び出しのみ
# - AuditLoggerは監査ログのみ

# Open/Closed Principle（開放/閉鎖の原則）
# - 抽象クラス（ABC）による拡張性
# - 新しいDB/AIプロバイダーは継承で追加

# Liskov Substitution Principle（リスコフの置換原則）
# - すべてのBridge実装は基底クラスと置換可能

# Interface Segregation Principle（インターフェース分離の原則）
# - 必要最小限のメソッドのみ定義

# Dependency Inversion Principle（依存性逆転の原則）
# - 上位モジュールはBridge抽象に依存
# - 具体的な実装には依存しない
```

### 2. 軽量性（Lite）

- **シンプル**: 複雑な機能は含めない
- **高速**: オーバーヘッド最小限
- **小規模**: コア機能のみ実装

### 3. テスタビリティ

- すべてのBridgeはモック実装を提供
- ユニットテスト可能な設計
- 統合テストとの分離

### 4. 拡張性

- プラグインアーキテクチャ
- 新しいプロバイダーの追加が容易
- 既存コードへの影響最小限

---

## 🏗️ アーキテクチャ

### システム全体図

```
┌─────────────────────────────────────────────┐
│         Resonant Engine Application         │
│  (FastAPI Backend / React Frontend / Daemon)│
└──────────────────┬──────────────────────────┘
                   │
                   ▼
    ┌──────────────────────────────────┐
    │       Bridge Lite Layer          │
    │  (抽象化・統一インターフェース)    │
    └──────────┬───────────┬───────────┘
               │           │
     ┌─────────▼───┐   ┌──▼──────────┐
     │ DataBridge  │   │  AIBridge   │
     │ (抽象)      │   │  (抽象)     │
     └──┬──────┬───┘   └──┬──────┬───┘
        │      │          │      │
   ┌────▼──┐ ┌▼────┐  ┌──▼───┐ ┌▼────┐
   │PgSQL  │ │Mock │  │Claude│ │GPT4 │
   │Bridge │ │Bridge│  │Bridge│ │Bridge│
   └───┬───┘ └─────┘  └───┬──┘ └─────┘
       │                  │
   ┌───▼────────┐    ┌───▼──────────┐
   │PostgreSQL  │    │ AI APIs      │
   │ Database   │    │ (Claude/GPT) │
   └────────────┘    └──────────────┘
```

### レイヤー構成

| レイヤー | 役割 | 例 |
|---------|------|-----|
| **Application Layer** | ビジネスロジック | FastAPI endpoints, Daemon |
| **Bridge Layer** | 抽象化・統一I/F | DataBridge, AIBridge |
| **Provider Layer** | 具体的実装 | PostgreSQLBridge, ClaudeBridge |
| **Infrastructure Layer** | 実際のリソース | PostgreSQL, Claude API |

### データフロー

```
┌─────────────┐
│   Message   │ ユーザー入力
└──────┬──────┘
       │
       ▼
┌──────────────┐
│Intent Detector│ Intent自動検出
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ DataBridge   │ Intent保存（DB抽象化）
│ .save_intent()│
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Daemon     │ 定期処理
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ DataBridge   │ 処理待ちIntent取得
│.get_pending()│
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  AIBridge    │ AI処理（Claude/GPT抽象化）
│  .call_ai()  │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ DataBridge   │ 結果保存
│.update_status│
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ AuditLogger  │ 全処理を記録
└──────────────┘
```

---

## 🧩 コンポーネント設計

### 1. DataBridge（データアクセス抽象化）

#### 責務
- データベースアクセスの抽象化
- Intent CRUD操作
- トランザクション管理

#### インターフェース

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime

class DataBridge(ABC):
    """データアクセス抽象化層"""
    
    @abstractmethod
    async def save_intent(
        self,
        intent_type: str,
        data: Dict[str, Any],
        status: str = "pending",
        source: str = "auto",
        user_id: Optional[str] = None
    ) -> str:
        """
        Intentを保存
        
        Args:
            intent_type: Intent種別（review/fix/test等）
            data: Intent詳細データ（JSONB）
            status: ステータス（pending/processing/completed/error）
            source: 発生源（auto_generated/manual/api）
            user_id: ユーザーID
        
        Returns:
            作成されたIntentのID
        
        Raises:
            BridgeError: 保存失敗時
        """
        pass
    
    @abstractmethod
    async def get_intent(self, intent_id: str) -> Optional[Dict[str, Any]]:
        """
        Intent取得
        
        Args:
            intent_id: IntentのID
        
        Returns:
            Intent情報、存在しない場合はNone
        """
        pass
    
    @abstractmethod
    async def get_pending_intents(
        self,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        処理待ちIntent一覧取得
        
        Args:
            limit: 取得件数上限
            offset: オフセット
        
        Returns:
            Intent情報のリスト
        """
        pass
    
    @abstractmethod
    async def update_intent_status(
        self,
        intent_id: str,
        status: str,
        result: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Intentステータス更新
        
        Args:
            intent_id: IntentのID
            status: 新しいステータス
            result: 処理結果（オプション）
        
        Returns:
            更新成功ならTrue
        """
        pass
    
    @abstractmethod
    async def save_message(
        self,
        content: str,
        sender: str,
        intent_id: Optional[str] = None,
        thread_id: Optional[str] = None
    ) -> str:
        """
        メッセージ保存
        
        Args:
            content: メッセージ内容
            sender: 送信者
            intent_id: 関連IntentのID
            thread_id: スレッドID
        
        Returns:
            作成されたメッセージのID
        """
        pass
    
    @abstractmethod
    async def get_messages(
        self,
        limit: int = 50,
        thread_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        メッセージ一覧取得
        
        Args:
            limit: 取得件数上限
            thread_id: スレッドIDでフィルタ（オプション）
        
        Returns:
            メッセージ情報のリスト
        """
        pass
```

#### 実装クラス

##### PostgreSQLBridge
```python
class PostgreSQLBridge(DataBridge):
    """PostgreSQL実装"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool = None
    
    async def connect(self):
        """接続プール初期化"""
        if not self.pool:
            import asyncpg
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=2,
                max_size=10
            )
    
    async def disconnect(self):
        """接続プールクローズ"""
        if self.pool:
            await self.pool.close()
            self.pool = None
    
    async def save_intent(
        self,
        intent_type: str,
        data: Dict[str, Any],
        status: str = "pending",
        source: str = "auto",
        user_id: Optional[str] = None
    ) -> str:
        """Intent保存（PostgreSQL実装）"""
        await self.connect()
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO intents (type, data, status, source, user_id)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
            """, intent_type, json.dumps(data), status, source, user_id)
            
            return str(row['id'])
    
    # 他のメソッドも同様に実装...
```

##### MockBridge
```python
class MockBridge(DataBridge):
    """テスト用モック実装"""
    
    def __init__(self):
        self.intents: Dict[str, Dict[str, Any]] = {}
        self.messages: Dict[str, Dict[str, Any]] = {}
    
    async def save_intent(
        self,
        intent_type: str,
        data: Dict[str, Any],
        status: str = "pending",
        source: str = "auto",
        user_id: Optional[str] = None
    ) -> str:
        """Intent保存（メモリ実装）"""
        import uuid
        intent_id = str(uuid.uuid4())
        
        self.intents[intent_id] = {
            'id': intent_id,
            'type': intent_type,
            'data': data,
            'status': status,
            'source': source,
            'user_id': user_id,
            'created_at': datetime.now()
        }
        
        return intent_id
    
    # 他のメソッドも同様に実装...
```

---

### 2. AIBridge（AI API抽象化）

#### 責務
- AI API呼び出しの抽象化
- プロンプト構築
- レスポンス処理

#### インターフェース

```python
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List

class AIBridge(ABC):
    """AI API抽象化層"""
    
    @abstractmethod
    async def call_ai(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> Optional[str]:
        """
        AI APIを呼び出す
        
        Args:
            prompt: ユーザープロンプト
            system_prompt: システムプロンプト（オプション）
            model: モデル名（None時はデフォルト）
            temperature: 温度パラメータ（0.0-1.0）
            max_tokens: 最大トークン数
        
        Returns:
            AIの応答テキスト、失敗時はNone
        
        Raises:
            AIBridgeError: API呼び出し失敗時
        """
        pass
    
    @abstractmethod
    async def call_ai_streaming(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7
    ) -> Any:
        """
        AI APIをストリーミングモードで呼び出す
        
        Args:
            prompt: ユーザープロンプト
            system_prompt: システムプロンプト
            model: モデル名
            temperature: 温度パラメータ
        
        Yields:
            テキストチャンク
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        モデル情報取得
        
        Returns:
            モデル名、プロバイダー、バージョン等
        """
        pass
```

#### 実装クラス

##### ClaudeBridge
```python
class ClaudeBridge(AIBridge):
    """Claude API実装"""
    
    def __init__(
        self,
        api_key: str,
        default_model: str = "claude-3-5-sonnet-20241022"
    ):
        import anthropic
        self.client = anthropic.Anthropic(api_key=api_key)
        self.default_model = default_model
    
    async def call_ai(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> Optional[str]:
        """Claude API呼び出し"""
        try:
            messages = [{"role": "user", "content": prompt}]
            
            kwargs = {
                "model": model or self.default_model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": messages
            }
            
            if system_prompt:
                kwargs["system"] = system_prompt
            
            response = self.client.messages.create(**kwargs)
            return response.content[0].text
            
        except Exception as e:
            raise AIBridgeError(f"Claude API error: {e}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """モデル情報"""
        return {
            "provider": "Anthropic",
            "model": self.default_model,
            "version": "3.5"
        }
```

##### GPT4Bridge
```python
class GPT4Bridge(AIBridge):
    """GPT-4 API実装（将来の拡張用）"""
    
    def __init__(
        self,
        api_key: str,
        default_model: str = "gpt-4-turbo"
    ):
        import openai
        self.client = openai.OpenAI(api_key=api_key)
        self.default_model = default_model
    
    async def call_ai(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> Optional[str]:
        """GPT-4 API呼び出し"""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model=model or self.default_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise AIBridgeError(f"GPT-4 API error: {e}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """モデル情報"""
        return {
            "provider": "OpenAI",
            "model": self.default_model,
            "version": "4"
        }
```

---

### 3. AuditLogger（監査ログ統合）

#### 責務
- すべてのBridge操作をログ記録
- トレーサビリティ確保
- デバッグ支援

#### インターフェース

```python
from datetime import datetime
from typing import Dict, Any, Optional
import json
from pathlib import Path

class AuditLogger:
    """監査ログ記録"""
    
    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = log_dir / f"audit_{datetime.now().strftime('%Y%m%d')}.log"
    
    def log_data_operation(
        self,
        operation: str,
        bridge_type: str,
        details: Dict[str, Any],
        user_id: Optional[str] = None
    ):
        """
        データ操作をログ記録
        
        Args:
            operation: 操作種別（save_intent/update_status等）
            bridge_type: Bridge種別（PostgreSQL/Mock等）
            details: 詳細情報
            user_id: ユーザーID
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "data_operation",
            "operation": operation,
            "bridge": bridge_type,
            "details": details,
            "user_id": user_id
        }
        self._write_log(entry)
    
    def log_ai_call(
        self,
        bridge_type: str,
        model: str,
        prompt_length: int,
        response_length: Optional[int],
        duration_ms: float,
        success: bool,
        error: Optional[str] = None
    ):
        """
        AI API呼び出しをログ記録
        
        Args:
            bridge_type: Bridge種別（Claude/GPT4等）
            model: モデル名
            prompt_length: プロンプト長
            response_length: レスポンス長（失敗時はNone）
            duration_ms: 処理時間（ミリ秒）
            success: 成功フラグ
            error: エラーメッセージ
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "ai_call",
            "bridge": bridge_type,
            "model": model,
            "prompt_length": prompt_length,
            "response_length": response_length,
            "duration_ms": duration_ms,
            "success": success,
            "error": error
        }
        self._write_log(entry)
    
    def _write_log(self, entry: Dict[str, Any]):
        """ログファイルに書き込み"""
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
```

---

### 4. BridgeFactory（ファクトリパターン）

#### 責務
- Bridge生成の一元化
- 設定ファイルからの自動生成
- 依存性注入

```python
from typing import Optional
import os

class BridgeFactory:
    """Bridge生成ファクトリ"""
    
    @staticmethod
    def create_data_bridge(
        bridge_type: Optional[str] = None,
        **kwargs
    ) -> DataBridge:
        """
        DataBridge生成
        
        Args:
            bridge_type: Bridge種別（postgresql/mock等）
            **kwargs: Bridge固有の引数
        
        Returns:
            DataBridgeインスタンス
        """
        bridge_type = bridge_type or os.getenv("DATA_BRIDGE_TYPE", "postgresql")
        
        if bridge_type == "postgresql":
            database_url = kwargs.get("database_url") or os.getenv("DATABASE_URL")
            return PostgreSQLBridge(database_url)
        
        elif bridge_type == "mock":
            return MockBridge()
        
        else:
            raise ValueError(f"Unknown bridge type: {bridge_type}")
    
    @staticmethod
    def create_ai_bridge(
        bridge_type: Optional[str] = None,
        **kwargs
    ) -> AIBridge:
        """
        AIBridge生成
        
        Args:
            bridge_type: Bridge種別（claude/gpt4等）
            **kwargs: Bridge固有の引数
        
        Returns:
            AIBridgeインスタンス
        """
        bridge_type = bridge_type or os.getenv("AI_BRIDGE_TYPE", "claude")
        
        if bridge_type == "claude":
            api_key = kwargs.get("api_key") or os.getenv("ANTHROPIC_API_KEY")
            return ClaudeBridge(api_key)
        
        elif bridge_type == "gpt4":
            api_key = kwargs.get("api_key") or os.getenv("OPENAI_API_KEY")
            return GPT4Bridge(api_key)
        
        elif bridge_type == "mock":
            return MockAIBridge()
        
        else:
            raise ValueError(f"Unknown AI bridge type: {bridge_type}")
```

---

### 5. 例外クラス

```python
class BridgeError(Exception):
    """Bridge基底例外"""
    pass

class DataBridgeError(BridgeError):
    """DataBridge例外"""
    pass

class AIBridgeError(BridgeError):
    """AIBridge例外"""
    pass

class BridgeConnectionError(BridgeError):
    """Bridge接続エラー"""
    pass

class BridgeTimeoutError(BridgeError):
    """Bridgeタイムアウト"""
    pass
```

---

## 📂 ディレクトリ構成

```
/bridge/
  ├── __init__.py                    # パッケージ初期化
  ├── README.md                      # Bridge Lite説明
  │
  ├── core/                          # コア機能
  │   ├── __init__.py
  │   ├── data_bridge.py             # DataBridge抽象クラス
  │   ├── ai_bridge.py               # AIBridge抽象クラス
  │   ├── audit_logger.py            # 監査ログ
  │   ├── exceptions.py              # 例外定義
  │   └── protocol.py                # Intent Protocol定義
  │
  ├── providers/                     # 実装プロバイダー
  │   ├── __init__.py
  │   ├── postgresql_bridge.py       # PostgreSQL実装
  │   ├── mock_bridge.py             # モック実装
  │   ├── claude_bridge.py           # Claude API実装
  │   ├── gpt4_bridge.py             # GPT-4 API実装
  │   └── mock_ai_bridge.py          # AI モック実装
  │
  ├── factory/                       # ファクトリ
  │   ├── __init__.py
  │   └── bridge_factory.py          # Bridge生成
  │
  ├── config/                        # 設定
  │   ├── bridge_config.json         # Bridge設定
  │   └── api_registry.json          # API登録情報
  │
  └── utils/                         # ユーティリティ
      ├── __init__.py
      ├── validator.py               # バリデーション
      └── serializer.py              # シリアライズ
```

---

## 🔧 実装仕様

### 設定ファイル

#### bridge_config.json
```json
{
  "version": "1.0.0",
  "data_bridge": {
    "type": "postgresql",
    "connection": {
      "database_url": "${DATABASE_URL}",
      "min_pool_size": 2,
      "max_pool_size": 10,
      "timeout": 30
    }
  },
  "ai_bridge": {
    "type": "claude",
    "default_model": "claude-3-5-sonnet-20241022",
    "temperature": 0.7,
    "max_tokens": 4096,
    "retry": {
      "max_attempts": 3,
      "backoff_factor": 2.0
    }
  },
  "audit_logger": {
    "enabled": true,
    "log_dir": "./logs/audit",
    "rotation": "daily",
    "retention_days": 30
  }
}
```

#### api_registry.json
```json
{
  "ai_providers": {
    "claude": {
      "endpoint": "https://api.anthropic.com/v1/messages",
      "auth_type": "api_key",
      "env_var": "ANTHROPIC_API_KEY",
      "models": [
        "claude-3-5-sonnet-20241022",
        "claude-3-opus-20240229"
      ]
    },
    "gpt4": {
      "endpoint": "https://api.openai.com/v1/chat/completions",
      "auth_type": "bearer",
      "env_var": "OPENAI_API_KEY",
      "models": [
        "gpt-4-turbo",
        "gpt-4"
      ]
    }
  }
}
```

### 環境変数

```bash
# .env

# データベース
DATABASE_URL=postgresql://resonant@localhost:5432/resonant
DATA_BRIDGE_TYPE=postgresql  # postgresql | mock

# AI API
ANTHROPIC_API_KEY=sk-ant-xxxxx
OPENAI_API_KEY=sk-xxxxx
AI_BRIDGE_TYPE=claude  # claude | gpt4 | mock

# ログ
BRIDGE_LOG_LEVEL=INFO
AUDIT_LOG_ENABLED=true
```

---

## 📊 使用例

### 基本的な使用方法

```python
from bridge.factory import BridgeFactory
from bridge.core import AuditLogger
from pathlib import Path

# Bridge初期化
data_bridge = BridgeFactory.create_data_bridge()
ai_bridge = BridgeFactory.create_ai_bridge()
audit_logger = AuditLogger(Path("./logs/audit"))

# Intent保存
intent_id = await data_bridge.save_intent(
    intent_type="review",
    data={
        "target": "main.py",
        "confidence": "high",
        "description": "コードレビュー要求"
    },
    source="auto_generated"
)

audit_logger.log_data_operation(
    operation="save_intent",
    bridge_type="PostgreSQL",
    details={"intent_id": intent_id, "type": "review"}
)

# 処理待ちIntent取得
pending_intents = await data_bridge.get_pending_intents(limit=5)

for intent in pending_intents:
    # AI処理
    prompt = f"Intent: {intent['type']}\nData: {intent['data']}"
    
    import time
    start = time.time()
    response = await ai_bridge.call_ai(prompt)
    duration_ms = (time.time() - start) * 1000
    
    audit_logger.log_ai_call(
        bridge_type="Claude",
        model="claude-3-5-sonnet-20241022",
        prompt_length=len(prompt),
        response_length=len(response) if response else None,
        duration_ms=duration_ms,
        success=response is not None
    )
    
    # ステータス更新
    await data_bridge.update_intent_status(
        intent_id=intent['id'],
        status="completed" if response else "error",
        result={"response": response}
    )
```

### FastAPI統合例

```python
from fastapi import FastAPI, Depends
from bridge.factory import BridgeFactory

app = FastAPI()

# Dependency Injection
def get_data_bridge():
    return BridgeFactory.create_data_bridge()

def get_ai_bridge():
    return BridgeFactory.create_ai_bridge()

@app.post("/api/messages")
async def create_message(
    message: MessageCreate,
    data_bridge: DataBridge = Depends(get_data_bridge)
):
    """メッセージ作成（Bridge経由）"""
    
    # メッセージ保存
    message_id = await data_bridge.save_message(
        content=message.content,
        sender=message.sender
    )
    
    # Intent自動検出
    from dashboard.backend.intent_detector import detect_intent_from_message
    intent_info = detect_intent_from_message(message.content)
    
    if intent_info:
        # Intent保存（Bridge経由）
        intent_id = await data_bridge.save_intent(
            intent_type=intent_info["type"],
            data=intent_info["data"],
            source="auto_generated"
        )
        
        # メッセージとIntent紐付け
        # (省略)
    
    return {"message_id": message_id}
```

### テストコード例

```python
import pytest
from bridge.providers import MockBridge, MockAIBridge

@pytest.mark.asyncio
async def test_intent_processing():
    """Intent処理テスト（モックBridge使用）"""
    
    # モックBridge初期化
    data_bridge = MockBridge()
    ai_bridge = MockAIBridge()
    
    # Intent保存
    intent_id = await data_bridge.save_intent(
        intent_type="review",
        data={"target": "test.py"}
    )
    
    assert intent_id is not None
    
    # Intent取得
    intent = await data_bridge.get_intent(intent_id)
    assert intent["type"] == "review"
    assert intent["status"] == "pending"
    
    # AI処理（モック）
    response = await ai_bridge.call_ai("Test prompt")
    assert response == "Mock AI Response"
    
    # ステータス更新
    success = await data_bridge.update_intent_status(
        intent_id=intent_id,
        status="completed"
    )
    assert success
    
    # 更新確認
    updated = await data_bridge.get_intent(intent_id)
    assert updated["status"] == "completed"
```

---

## 🚀 移行計画

### Phase 1: Bridge Lite基盤構築（1-2日）

**目標**: コア機能の実装

**タスク**:
1. ディレクトリ構成作成
2. 抽象クラス実装（DataBridge/AIBridge）
3. PostgreSQLBridge実装
4. ClaudeBridge実装
5. MockBridge実装（テスト用）
6. BridgeFactory実装
7. 基本的なユニットテスト

**成果物**:
- `/bridge/core/` - コアクラス
- `/bridge/providers/` - 実装プロバイダー
- `/bridge/factory/` - ファクトリ
- `/tests/bridge/` - ユニットテスト

### Phase 2: 既存コード移行（2-3日）

**目標**: 既存のPostgreSQL直接依存を排除

**タスク**:
1. `intent_processor_db.py`をBridge経由に書き換え
2. `main.py`（FastAPI）をBridge経由に書き換え
3. `resonant_daemon_db.py`をBridge経由に書き換え
4. 統合テスト実施
5. パフォーマンステスト

**影響範囲**:
- `/dashboard/backend/intent_processor_db.py`
- `/dashboard/backend/main.py`
- `/daemon/resonant_daemon_db.py`

### Phase 3: 監査ログ統合（1-2日）

**目標**: ログの一元化

**タスク**:
1. AuditLogger実装
2. 全Bridge操作にログ追加
3. ログ分析ツール作成
4. ドキュメント更新

**成果物**:
- `/bridge/core/audit_logger.py`
- `/logs/audit/` - 監査ログディレクトリ
- ログ分析スクリプト

### Phase 4: ドキュメント・テスト完成（1日）

**目標**: 品質保証

**タスク**:
1. API仕様書作成
2. 使用例ドキュメント作成
3. トラブルシューティングガイド
4. カバレッジ100%達成

**成果物**:
- `/docs/bridge_lite_api.md`
- `/docs/bridge_lite_examples.md`
- `/docs/bridge_lite_troubleshooting.md`

---

## 🧪 テスト戦略

### ユニットテスト

```python
# tests/bridge/test_data_bridge.py

import pytest
from bridge.providers import PostgreSQLBridge, MockBridge

@pytest.fixture
def mock_bridge():
    return MockBridge()

@pytest.mark.asyncio
async def test_save_intent(mock_bridge):
    """Intent保存テスト"""
    intent_id = await mock_bridge.save_intent(
        intent_type="review",
        data={"target": "test.py"}
    )
    
    assert intent_id is not None
    
    # 保存確認
    intent = await mock_bridge.get_intent(intent_id)
    assert intent["type"] == "review"
    assert intent["data"]["target"] == "test.py"

@pytest.mark.asyncio
async def test_get_pending_intents(mock_bridge):
    """処理待ちIntent取得テスト"""
    # 複数Intent作成
    ids = []
    for i in range(5):
        intent_id = await mock_bridge.save_intent(
            intent_type=f"type{i}",
            data={"index": i}
        )
        ids.append(intent_id)
    
    # 取得
    pending = await mock_bridge.get_pending_intents(limit=3)
    
    assert len(pending) == 3
    assert all(intent["status"] == "pending" for intent in pending)
```

### 統合テスト

```python
# tests/integration/test_bridge_integration.py

import pytest
from bridge.factory import BridgeFactory
import os

@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_intent_flow():
    """Intent処理フルフローテスト"""
    
    # 実際のBridge使用
    os.environ["DATA_BRIDGE_TYPE"] = "postgresql"
    os.environ["AI_BRIDGE_TYPE"] = "claude"
    
    data_bridge = BridgeFactory.create_data_bridge()
    ai_bridge = BridgeFactory.create_ai_bridge()
    
    # Intent保存
    intent_id = await data_bridge.save_intent(
        intent_type="review",
        data={"target": "integration_test.py"}
    )
    
    # Intent取得
    intent = await data_bridge.get_intent(intent_id)
    assert intent is not None
    
    # AI処理
    response = await ai_bridge.call_ai(
        f"Review: {intent['data']['target']}"
    )
    assert response is not None
    
    # ステータス更新
    success = await data_bridge.update_intent_status(
        intent_id=intent_id,
        status="completed",
        result={"response": response}
    )
    assert success
```

### パフォーマンステスト

```python
# tests/performance/test_bridge_performance.py

import pytest
import time
from bridge.factory import BridgeFactory

@pytest.mark.performance
@pytest.mark.asyncio
async def test_concurrent_intent_creation():
    """並行Intent作成パフォーマンステスト"""
    import asyncio
    
    data_bridge = BridgeFactory.create_data_bridge()
    
    async def create_intent(i):
        return await data_bridge.save_intent(
            intent_type="test",
            data={"index": i}
        )
    
    start = time.time()
    
    # 100件並行作成
    tasks = [create_intent(i) for i in range(100)]
    results = await asyncio.gather(*tasks)
    
    duration = time.time() - start
    
    assert len(results) == 100
    assert duration < 5.0  # 5秒以内に完了
    print(f"✅ Created 100 intents in {duration:.2f}s")
```

---

## 📈 メトリクス・監視

### 監視指標

| 指標 | 目標値 | 測定方法 |
|------|--------|----------|
| **Intent保存レイテンシ** | < 100ms | AuditLogger |
| **AI API呼び出しレイテンシ** | < 3s | AuditLogger |
| **データベース接続プール使用率** | < 80% | PostgreSQLBridge |
| **エラー率** | < 1% | 例外ログ |
| **ログファイルサイズ** | < 100MB/日 | ログローテーション |

### ログ出力例

```json
// データ操作ログ
{
  "timestamp": "2025-11-12T18:30:45.123456",
  "type": "data_operation",
  "operation": "save_intent",
  "bridge": "PostgreSQL",
  "details": {
    "intent_id": "a1b2c3d4-...",
    "intent_type": "review",
    "status": "pending"
  },
  "user_id": null
}

// AI呼び出しログ
{
  "timestamp": "2025-11-12T18:30:50.654321",
  "type": "ai_call",
  "bridge": "Claude",
  "model": "claude-3-5-sonnet-20241022",
  "prompt_length": 1234,
  "response_length": 5678,
  "duration_ms": 2345.67,
  "success": true,
  "error": null
}
```

---

## 🔒 セキュリティ考慮事項

### 1. API Key管理
- 環境変数での管理
- コードに直接記述しない
- `.env`ファイルは`.gitignore`に追加

### 2. ログセキュリティ
- 機密情報（API Key等）をログに記録しない
- ユーザーデータは最小限に
- ログファイルのアクセス権限管理

### 3. データベースセキュリティ
- SQLインジェクション対策（パラメータ化クエリ）
- 接続プールの適切な管理
- トランザクション分離レベルの設定

---

## 📚 参考資料

### 設計パターン
- **Bridge Pattern**: 抽象化と実装の分離
- **Factory Pattern**: オブジェクト生成の一元化
- **Strategy Pattern**: アルゴリズムの切り替え

### 関連ドキュメント
- `/docs/work_log_20251112.md` - 本日の作業記録
- `/docs/technical_review_response_20251112.md` - 技術レビュー対応
- `/docs/bridge_architecture_evaluation_20251112.md` - Bridgeアーキテクチャ評価

---

## 📝 更新履歴

| 日付 | バージョン | 変更内容 | 担当 |
|------|-----------|---------|------|
| 2025-11-12 | 1.0.0 | 初版作成 | GitHub Copilot |

---

**ドキュメント終了**
