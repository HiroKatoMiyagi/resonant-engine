# エラーリカバリー実装完了報告

**作成日**: 2025-11-06  
**対象**: Event Schema拡張 + エラーリカバリー強化

---

## 📋 実装内容

### 1. Event Schema拡張

#### 追加されたフィールド

- **`status`**: ステータス管理（pending/running/success/failed/retrying）
- **`error_info`**: エラー情報の構造化
  - `error_type`: エラーの型名
  - `error_message`: エラーメッセージ
  - `error_category`: エラー分類（network/rate_limit/api_error/auth_error/validation/unknown）
  - `stack_trace`: スタックトレース
- **`retry_info`**: リトライ情報
  - `retry_count`: リトライ回数
  - `max_retries`: 最大リトライ回数
  - `retryable`: リトライ可能かどうか
  - `next_retry_at`: 次回リトライ予定時刻（将来拡張用）

#### イベントタイプの拡張

- **`error`**: エラーイベント（専用）
- **`retry`**: リトライイベント

#### Event Type Taxonomy

ドキュメントに追加：
- intent: 人間またはAIの意図表明
- action: システムの行動
- result: 行動の結果
- observation: 観測・監視イベント
- hypothesis: 仮説の記録・更新
- **error**: エラーイベント（新規）
- **retry**: リトライイベント（新規）

---

### 2. エラーリカバリーモジュール (`utils/error_recovery.py`)

#### 主要クラス

##### `ErrorCategory` (Enum)

エラー分類:
- `NETWORK`: ネットワークエラー（リトライ可能）
- `API_RATE_LIMIT`: APIレート制限（リトライ可能、長時間待機）
- `API_ERROR`: APIエラー（リトライ可能）
- `AUTH_ERROR`: 認証エラー（リトライ不可）
- `VALIDATION_ERROR`: 検証エラー（リトライ不可）
- `UNKNOWN`: 不明なエラー

##### `RetryStrategy`

指数バックオフによるリトライ戦略:
- `max_retries`: 最大リトライ回数
- `initial_delay`: 初期待機時間
- `max_delay`: 最大待機時間
- `exponential_base`: 指数の底
- `jitter`: ジッター（ランダム要素）の有無

##### `ErrorClassifier`

エラー分類器:
- `classify_error()`: エラーを分類
- `is_retryable()`: リトライ可能かどうかを判定
- `get_recovery_strategy()`: エラー分類に応じたリカバリー戦略を取得

##### `DeadLetterQueue`

デッドレターキュー:
- `add()`: リトライ不可能なエラーを追加
- `get_failed_events()`: 失敗したイベントを取得

##### `with_retry()`

自動リトライデコレータ関数:
- 指数バックオフによる自動リトライ
- エラー分類に応じた戦略の適用
- リトライ/失敗時のコールバック

---

### 3. Notion統合エージェントへの統合

#### 実装内容

`utils/notion_sync_agent.py` に以下を統合:

1. **自動リトライメカニズム**
   - `get_specs_with_sync_trigger()` に指数バックオフを実装
   - エラー分類に応じたリトライ戦略の適用

2. **エラー情報の構造化**
   - エラー発生時に `error_info` フィールドに詳細情報を記録
   - スタックトレースの記録

3. **リトライ情報の記録**
   - リトライ時に `retry` イベントを記録
   - `retry_info` フィールドにリトライ情報を記録

4. **デッドレターキューの統合**
   - リトライ不可能なエラーをデッドレターキューに追加

5. **ヘルパーメソッド**
   - `_handle_retry()`: リトライ時の処理
   - `_handle_failure()`: 最終失敗時の処理

---

## 📊 実装統計

### 新規ファイル

- `utils/error_recovery.py`: 約400行

### 更新ファイル

- `utils/resonant_event_stream.py`: イベントスキーマ拡張
- `utils/notion_sync_agent.py`: エラーリカバリー統合

---

## 🔍 使用例

### 基本的な使用

```python
from utils.error_recovery import with_retry, RetryStrategy, ErrorClassifier

def api_call():
    # API呼び出し
    response = client.request(...)
    return response

# 自動リトライ付きで実行
try:
    result = with_retry(
        api_call,
        strategy=RetryStrategy(max_retries=3, initial_delay=1.0),
        on_retry=lambda attempt, error: print(f"リトライ {attempt}: {error}"),
        on_failure=lambda error: print(f"最終失敗: {error}")
    )
except Exception as e:
    # 最終的に失敗した場合
    pass
```

### エラー分類の使用

```python
from utils.error_recovery import ErrorClassifier

error = ConnectionError("Network timeout")
category = ErrorClassifier.classify_error(error)
print(category)  # ErrorCategory.NETWORK

is_retryable = ErrorClassifier.is_retryable(error)
print(is_retryable)  # True

strategy = ErrorClassifier.get_recovery_strategy(category)
```

### デッドレターキューの使用

```python
from utils.error_recovery import DeadLetterQueue

dlq = DeadLetterQueue()

# リトライ不可能なエラーを追加
dlq.add(
    event_id="EVT-12345",
    error=ValueError("Invalid input"),
    error_category=ErrorCategory.VALIDATION_ERROR,
    context={"action": "validate", "input": "..."},
    retry_count=0
)

# 失敗したイベントを取得
failed_events = dlq.get_failed_events(since=datetime.now() - timedelta(days=1))
```

---

## ✅ 動作確認

### テスト項目

- [x] エラー分類が正しく動作する
- [x] 指数バックオフが正しく動作する
- [x] リトライイベントが記録される
- [x] エラー情報が構造化されて記録される
- [x] デッドレターキューが正しく動作する
- [x] イベントスキーマが拡張されている

---

## 📝 次のステップ

### 将来的な拡張

1. **動的リトライ戦略**
   - エラー発生時に動的に戦略を変更

2. **リトライスケジューリング**
   - `next_retry_at` フィールドの活用
   - 非同期リトライの実装

3. **メトリクス収集**
   - リトライ成功率の追跡
   - エラー率の監視

4. **アラート機能**
   - デッドレターキューに追加された場合の通知

---

**作成**: 2025-11-06  
**作成者**: Claude Sonnet 4.5  
**プロジェクト**: Resonant Engine v1.1

