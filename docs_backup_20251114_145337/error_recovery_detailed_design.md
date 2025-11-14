# エラーリカバリー機能 詳細設計書

**プロジェクト**: Resonant Engine v1.1  
**作成日**: 2025-11-06  
**対象機能**: Event Schema拡張 + エラーリカバリー強化

---

## 📋 目次

1. [モジュール詳細仕様](#モジュール詳細仕様)
2. [API仕様](#api仕様)
3. [アルゴリズム詳細](#アルゴリズム詳細)
4. [処理フロー](#処理フロー)
5. [エラーハンドリング](#エラーハンドリング)

---

## モジュール詳細仕様

### 1. ErrorCategory (Enum)

#### 定義

```python
class ErrorCategory(Enum):
    NETWORK = "network"
    API_RATE_LIMIT = "rate_limit"
    API_ERROR = "api_error"
    AUTH_ERROR = "auth_error"
    VALIDATION_ERROR = "validation"
    UNKNOWN = "unknown"
```

#### 分類ロジック

| カテゴリ | 判定キーワード | リトライ可能 | 説明 |
|---------|---------------|------------|------|
| NETWORK | "connection", "timeout", "network", "unreachable" | ✅ | ネットワーク関連エラー |
| API_RATE_LIMIT | "rate limit", "429", "too many requests", "quota" | ✅ | APIレート制限 |
| AUTH_ERROR | "401", "403", "unauthorized", "forbidden", "authentication" | ❌ | 認証・認可エラー |
| API_ERROR | "api", "500", "502", "503", "504", "service" | ✅ | サーバーエラー |
| VALIDATION_ERROR | "validation", "invalid", "400", "bad request" | ❌ | 入力検証エラー |
| UNKNOWN | 上記以外 | ❓ | 分類不明 |

---

### 2. RetryStrategy

#### クラス定義

```python
class RetryStrategy:
    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    )
```

#### メソッド

##### `get_delay(attempt: int) -> float`

**目的**: リトライ待機時間を計算（指数バックオフ）

**アルゴリズム**:
```
1. delay = initial_delay * (exponential_base ^ attempt)
2. delay = min(delay, max_delay)
3. if jitter:
       jitter_factor = 0.8 + (random() * 0.4)  # 0.8〜1.2倍
       delay = delay * jitter_factor
4. return delay
```

**例**:
- attempt=0: delay = 1.0 * 2^0 = 1.0秒（ジッター適用後: 0.8〜1.2秒）
- attempt=1: delay = 1.0 * 2^1 = 2.0秒（ジッター適用後: 1.6〜2.4秒）
- attempt=2: delay = 1.0 * 2^2 = 4.0秒（ジッター適用後: 3.2〜4.8秒）

---

### 3. ErrorClassifier

#### 静的メソッド

##### `classify_error(error: Exception) -> ErrorCategory`

**目的**: エラーを分類

**処理フロー**:
1. エラーメッセージを小文字に変換
2. エラータイプ名を取得
3. キーワードマッチングで分類
4. 分類結果を返却

**優先順位**:
1. ネットワークエラー
2. レート制限
3. 認証エラー
4. APIエラー
5. 検証エラー
6. 不明なエラー

##### `is_retryable(error: Exception) -> bool`

**目的**: リトライ可能かどうかを判定

**ロジック**:
```python
category = classify_error(error)
return category in [NETWORK, API_RATE_LIMIT, API_ERROR]
```

##### `get_recovery_strategy(category: ErrorCategory) -> RetryStrategy`

**目的**: エラー分類に応じたリカバリー戦略を取得

**戦略マッピング**:

| カテゴリ | max_retries | initial_delay | max_delay | 説明 |
|---------|-------------|---------------|-----------|------|
| API_RATE_LIMIT | 5 | 5.0秒 | 300.0秒 | レート制限は長めの待機 |
| NETWORK | 3 | 1.0秒 | 60.0秒 | ネットワークエラーは中程度 |
| API_ERROR | 3 | 0.5秒 | 30.0秒 | APIエラーは短め |
| その他 | 0 | - | - | リトライ不可 |

---

### 4. DeadLetterQueue

#### クラス定義

```python
class DeadLetterQueue:
    def __init__(self, dlq_path: Path = None):
        self.dlq_path = dlq_path or Path("logs/dead_letter_queue.jsonl")
```

#### メソッド

##### `add(event_id, error, error_category, context, retry_count)`

**目的**: デッドレターキューに追加

**パラメータ**:
- `event_id` (str): イベントID
- `error` (Exception): 例外オブジェクト
- `error_category` (ErrorCategory): エラー分類
- `context` (Dict[str, Any]): コンテキスト情報
- `retry_count` (int): リトライ回数

**保存形式**:
```json
{
  "event_id": "EVT-...",
  "timestamp": "2025-11-06T09:00:00",
  "error_type": "ValueError",
  "error_message": "...",
  "error_category": "validation",
  "retry_count": 0,
  "context": {...}
}
```

##### `get_failed_events(since: Optional[datetime] = None) -> List[Dict]`

**目的**: 失敗したイベントを取得

**パラメータ**:
- `since` (Optional[datetime]): この日時以降のイベントのみ

**戻り値**: 失敗したイベントのリスト

---

### 5. with_retry()

#### 関数シグネチャ

```python
def with_retry(
    func: Callable,
    strategy: Optional[RetryStrategy] = None,
    error_context: Optional[Dict[str, Any]] = None,
    on_retry: Optional[Callable[[int, Exception], None]] = None,
    on_failure: Optional[Callable[[Exception], None]] = None
) -> Any
```

#### 処理フロー

```
1. strategyがNoneの場合はデフォルト戦略を設定
2. for attempt in range(0, max_retries + 1):
   a. try:
         result = func()
         return result
   b. except Exception as e:
         - リトライ不可能なエラー → 即座に例外を投げる
         - attempt >= max_retries → 例外を投げる
         - on_retryコールバックを実行
         - delay = strategy.get_delay(attempt)
         - time.sleep(delay)
3. 最終的に失敗した場合、on_failureコールバックを実行して例外を投げる
```

#### 使用例

```python
result = with_retry(
    api_call,
    strategy=RetryStrategy(max_retries=3),
    on_retry=lambda attempt, error: print(f"リトライ {attempt}: {error}"),
    on_failure=lambda error: print(f"最終失敗: {error}")
)
```

---

### 6. Event Stream Extension

#### emit() メソッドの拡張

**追加パラメータ**:
- `status` (Optional[str]): ステータス
- `error_info` (Optional[Dict[str, Any]]): エラー情報
- `retry_info` (Optional[Dict[str, Any]]): リトライ情報

**ステータスの自動判定**:
```python
if status is None:
    if exit_code is not None:
        status = "success" if exit_code == 0 else "failed"
    elif error_info:
        status = "failed"
    elif retry_info:
        status = "retrying"
    else:
        status = "pending"
```

**error_info 構造**:
```python
{
    "error_type": str,          # エラーの型名
    "error_message": str,       # エラーメッセージ
    "error_category": str,      # エラー分類（network/rate_limit等）
    "stack_trace": str          # スタックトレース
}
```

**retry_info 構造**:
```python
{
    "retry_count": int,         # リトライ回数
    "max_retries": int,         # 最大リトライ回数
    "retryable": bool,          # リトライ可能かどうか
    "next_retry_at": str        # 次回リトライ予定時刻（将来拡張用）
}
```

---

## API仕様

### Error Recovery Module API

#### ErrorClassifier

```python
# エラー分類
category = ErrorClassifier.classify_error(error)

# リトライ可能かどうか
is_retryable = ErrorClassifier.is_retryable(error)

# リカバリー戦略取得
strategy = ErrorClassifier.get_recovery_strategy(category)
```

#### RetryStrategy

```python
# 戦略作成
strategy = RetryStrategy(
    max_retries=3,
    initial_delay=1.0,
    max_delay=60.0,
    exponential_base=2.0,
    jitter=True
)

# 待機時間計算
delay = strategy.get_delay(attempt)
```

#### DeadLetterQueue

```python
# キュー作成
dlq = DeadLetterQueue()

# エラー追加
dlq.add(event_id, error, category, context, retry_count)

# 失敗イベント取得
events = dlq.get_failed_events(since=datetime.now() - timedelta(days=1))
```

#### with_retry()

```python
# 基本使用
result = with_retry(func)

# カスタム戦略
result = with_retry(
    func,
    strategy=RetryStrategy(max_retries=5),
    on_retry=lambda a, e: print(f"リトライ {a}"),
    on_failure=lambda e: print(f"失敗: {e}")
)
```

---

## アルゴリズム詳細

### 指数バックオフアルゴリズム

#### 基本式

```
delay(n) = initial_delay * (exponential_base ^ n)
delay(n) = min(delay(n), max_delay)
```

#### ジッター適用

```
if jitter:
    jitter_factor = random(0.8, 1.2)
    delay(n) = delay(n) * jitter_factor
```

#### 例: initial_delay=1.0, exponential_base=2.0, max_delay=60.0

| attempt | 基本待機時間 | ジッター適用後 | 最終待機時間 |
|---------|------------|--------------|------------|
| 0 | 1.0秒 | 0.8〜1.2秒 | 1.0秒（平均） |
| 1 | 2.0秒 | 1.6〜2.4秒 | 2.0秒（平均） |
| 2 | 4.0秒 | 3.2〜4.8秒 | 4.0秒（平均） |
| 3 | 8.0秒 | 6.4〜9.6秒 | 8.0秒（平均） |
| 4 | 16.0秒 | 12.8〜19.2秒 | 16.0秒（平均） |
| 5 | 32.0秒 | 25.6〜38.4秒 | 32.0秒（平均） |
| 6 | 64.0秒 | 51.2〜76.8秒 | 60.0秒（max_delay） |

### エラー分類アルゴリズム

#### キーワードマッチング

```python
def classify_error(error):
    error_str = str(error).lower()
    
    # 優先順位順にチェック
    if "connection" in error_str or "timeout" in error_str:
        return NETWORK
    if "rate limit" in error_str or "429" in error_str:
        return API_RATE_LIMIT
    if "401" in error_str or "unauthorized" in error_str:
        return AUTH_ERROR
    if "500" in error_str or "api" in error_str:
        return API_ERROR
    if "validation" in error_str or "400" in error_str:
        return VALIDATION_ERROR
    
    return UNKNOWN
```

---

## 処理フロー

### リトライ処理フロー

```
[関数実行]
    ↓
[エラー発生]
    ↓
[ErrorClassifier.classify_error()]
    ↓
[is_retryable() チェック]
    ↓
[リトライ不可能] → [例外を投げる]
    ↓
[リトライ可能]
    ↓
[RetryStrategy.get_delay() で待機時間計算]
    ↓
[指数バックオフ待機]
    ↓
[on_retry コールバック実行]
    ↓
[リトライ実行]
    ↓
[成功] → [結果を返す]
    ↓
[失敗] → [次のリトライ or 最終失敗]
```

### エラー記録フロー

```
[エラー発生]
    ↓
[error_info 構築]
    ├─ error_type
    ├─ error_message
    ├─ error_category
    └─ stack_trace
    ↓
[retry_info 構築]
    ├─ retry_count
    ├─ max_retries
    └─ retryable
    ↓
[イベントストリームに記録]
    ├─ status: "failed" or "retrying"
    ├─ error_info
    └─ retry_info
    ↓
[リトライ不可能な場合]
    ↓
[デッドレターキューに追加]
```

---

## エラーハンドリング

### エラー分類のエラーハンドリング

- エラー分類に失敗した場合: `UNKNOWN` を返す
- エラーメッセージが空の場合: `UNKNOWN` を返す

### リトライ処理のエラーハンドリング

- 待機時間計算エラー: デフォルト値（1.0秒）を使用
- コールバック実行エラー: ログに記録して続行

### デッドレターキューのエラーハンドリング

- ファイル書き込みエラー: 例外を発生
- ファイル読み込みエラー: 空のリストを返す
- JSON解析エラー: スキップして続行

---

## パフォーマンス考慮事項

### リトライによる待機時間

- 最大リトライ回数: 3回（デフォルト）
- 最大待機時間: 60秒（デフォルト）
- 合計最大待機時間: 約1.0 + 2.0 + 4.0 = 7秒（ジッター除く）

### メモリ使用量

- デッドレターキュー: JSONL形式で逐次書き込み（メモリ効率的）
- イベントストリーム: JSONL形式で逐次書き込み（メモリ効率的）

### ファイルI/O

- イベントストリーム: 追記モード（高速）
- デッドレターキュー: 追記モード（高速）

---

**作成**: 2025-11-06  
**作成者**: Claude Sonnet 4.5  
**プロジェクト**: Resonant Engine v1.1

