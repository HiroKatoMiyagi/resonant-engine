# エラーリカバリー機能 基本設計書

**プロジェクト**: Resonant Engine v1.1  
**作成日**: 2025-11-06  
**対象機能**: Event Schema拡張 + エラーリカバリー強化

---

## 📋 目次

1. [概要](#概要)
2. [設計目標](#設計目標)
3. [アーキテクチャ概要](#アーキテクチャ概要)
4. [主要コンポーネント](#主要コンポーネント)
5. [データ構造](#データ構造)

---

## 概要

統一イベントストリームの拡張と、エラー発生時の自動リカバリーメカニズムを実装しました。

### 実装背景

- エラー情報の構造化による分析の容易化
- 自動リトライによる堅牢性の向上
- デッドレターキューによるリトライ不可能なエラーの管理

---

## 設計目標

### 1. エラー情報の構造化

- エラー情報を構造化して記録
- エラー分類による適切なリカバリー戦略の選択
- スタックトレースの記録によるデバッグの容易化

### 2. 自動リトライメカニズム

- 指数バックオフによる自動リトライ
- エラー分類に応じた最適なリトライ戦略の適用
- リトライ不可能なエラーの早期検出

### 3. デッドレターキュー

- リトライ不可能なエラーの保存
- エラー分析と改善のためのデータ収集

---

## アーキテクチャ概要

### データフロー

```
[API呼び出し]
    ↓
[with_retry デコレータ]
    ↓
[エラー発生]
    ↓
[ErrorClassifier - エラー分類]
    ↓
[RetryStrategy - リトライ戦略選択]
    ↓
[指数バックオフ待機]
    ↓
[リトライ実行]
    ↓
[成功] → [イベントストリームに記録]
    ↓
[失敗] → [デッドレターキューに追加]
```

### イベントストリームの拡張

```
[イベント構造]
├─ 基本情報
│  ├─ event_id
│  ├─ timestamp
│  ├─ event_type
│  └─ source
├─ 拡張情報（新規）
│  ├─ status (pending/running/success/failed/retrying)
│  ├─ error_info (構造化されたエラー情報)
│  └─ retry_info (リトライ情報)
└─ 既存情報
   ├─ data
   ├─ parent_event_id
   └─ tags
```

---

## 主要コンポーネント

### 1. Error Recovery Module (`utils/error_recovery.py`)

#### 1.1 ErrorCategory (Enum)

エラーを6つのカテゴリに分類：

| カテゴリ | 説明 | リトライ可能 |
|---------|------|------------|
| `NETWORK` | ネットワークエラー | ✅ |
| `API_RATE_LIMIT` | APIレート制限 | ✅ |
| `API_ERROR` | APIエラー | ✅ |
| `AUTH_ERROR` | 認証エラー | ❌ |
| `VALIDATION_ERROR` | 検証エラー | ❌ |
| `UNKNOWN` | 不明なエラー | ❓ |

#### 1.2 RetryStrategy

指数バックオフによるリトライ戦略：

- **パラメータ**:
  - `max_retries`: 最大リトライ回数（デフォルト: 3）
  - `initial_delay`: 初期待機時間（デフォルト: 1.0秒）
  - `max_delay`: 最大待機時間（デフォルト: 60.0秒）
  - `exponential_base`: 指数の底（デフォルト: 2.0）
  - `jitter`: ジッター（ランダム要素）の有無（デフォルト: True）

- **待機時間計算**:
  ```
  delay = initial_delay * (exponential_base ^ attempt)
  delay = min(delay, max_delay)
  if jitter:
      delay = delay * (0.8 + random() * 0.4)
  ```

#### 1.3 ErrorClassifier

エラー分類器：

- **`classify_error(error)`**: エラーを分類
- **`is_retryable(error)`**: リトライ可能かどうかを判定
- **`get_recovery_strategy(category)`**: エラー分類に応じたリカバリー戦略を取得

#### 1.4 DeadLetterQueue

デッドレターキュー：

- **`add()`**: リトライ不可能なエラーを追加
- **`get_failed_events()`**: 失敗したイベントを取得

#### 1.5 with_retry()

自動リトライデコレータ関数：

- 指数バックオフによる自動リトライ
- エラー分類に応じた戦略の適用
- リトライ/失敗時のコールバック

### 2. Event Stream Extension (`utils/resonant_event_stream.py`)

#### 2.1 追加フィールド

- **`status`**: ステータス管理
  - `pending`: 待機中
  - `running`: 実行中
  - `success`: 成功
  - `failed`: 失敗
  - `retrying`: リトライ中

- **`error_info`**: エラー情報
  ```python
  {
      "error_type": str,
      "error_message": str,
      "error_category": str,
      "stack_trace": str
  }
  ```

- **`retry_info`**: リトライ情報
  ```python
  {
      "retry_count": int,
      "max_retries": int,
      "retryable": bool,
      "next_retry_at": str  # 将来拡張用
  }
  ```

### 3. Notion統合エージェントへの統合 (`utils/notion_sync_agent.py`)

#### 3.1 実装内容

- 自動リトライメカニズムの統合
- エラー情報の構造化記録
- リトライ情報の記録
- デッドレターキューへの追加

#### 3.2 ヘルパーメソッド

- **`_handle_retry()`**: リトライ時の処理
- **`_handle_failure()`**: 最終失敗時の処理

---

## データ構造

### イベントスキーマ（拡張版）

```json
{
  "event_id": "EVT-20251106-090000-abc123",
  "timestamp": "2025-11-06T09:00:00.123456",
  "event_type": "result",
  "source": "notion_sync",
  "data": {
    "status": "error",
    "error": "Connection timeout"
  },
  "parent_event_id": "EVT-20251106-085900-xyz789",
  "related_hypothesis_id": null,
  "tags": ["notion", "error"],
  "latency_ms": 5000,
  "exit_code": 1,
  "importance": 3,
  "status": "failed",
  "error_info": {
    "error_type": "ConnectionError",
    "error_message": "Connection timeout",
    "error_category": "network",
    "stack_trace": "..."
  },
  "retry_info": {
    "retry_count": 3,
    "max_retries": 3,
    "retryable": true
  }
}
```

### デッドレターキューエントリ

```json
{
  "event_id": "EVT-20251106-090000-abc123",
  "timestamp": "2025-11-06T09:00:00.123456",
  "error_type": "ValueError",
  "error_message": "Invalid input",
  "error_category": "validation",
  "retry_count": 0,
  "context": {
    "action": "fetch_specs",
    "database": "specs",
    "database_id": "..."
  }
}
```

---

## エラー分類ロジック

### 分類ルール

1. **ネットワークエラー**:
   - キーワード: "connection", "timeout", "network", "unreachable"

2. **レート制限**:
   - キーワード: "rate limit", "429", "too many requests", "quota"

3. **認証エラー**:
   - キーワード: "401", "403", "unauthorized", "forbidden", "authentication"

4. **APIエラー**:
   - キーワード: "api", "500", "502", "503", "504", "service"

5. **検証エラー**:
   - キーワード: "validation", "invalid", "400", "bad request"

6. **不明なエラー**:
   - 上記に該当しないすべてのエラー

---

## リトライ戦略の選択

### エラー分類別の戦略

| エラー分類 | max_retries | initial_delay | max_delay | 説明 |
|-----------|-------------|---------------|-----------|------|
| API_RATE_LIMIT | 5 | 5.0秒 | 300.0秒 | レート制限は長めの待機 |
| NETWORK | 3 | 1.0秒 | 60.0秒 | ネットワークエラーは中程度 |
| API_ERROR | 3 | 0.5秒 | 30.0秒 | APIエラーは短め |
| その他 | 0 | - | - | リトライ不可 |

---

## 統合ポイント

### 1. Notion統合エージェント

- `get_specs_with_sync_trigger()` に自動リトライを実装
- エラー発生時に構造化されたエラー情報を記録
- リトライ不可能なエラーはデッドレターキューに追加

### 2. イベントストリーム

- `emit()` メソッドに `status`, `error_info`, `retry_info` パラメータを追加
- ステータスの自動判定機能

---

## 拡張性

### 将来の拡張予定

1. **動的リトライ戦略**:
   - エラー発生時に動的に戦略を変更

2. **リトライスケジューリング**:
   - `next_retry_at` フィールドの活用
   - 非同期リトライの実装

3. **メトリクス収集**:
   - リトライ成功率の追跡
   - エラー率の監視

4. **アラート機能**:
   - デッドレターキューに追加された場合の通知

---

**作成**: 2025-11-06  
**作成者**: Claude Sonnet 4.5  
**プロジェクト**: Resonant Engine v1.1

