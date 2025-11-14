# P0改善: Event Schema拡張とエラーリカバリー強化

## 概要

このP0改善では、以下の2つの主要な機能を実装しました：

1. **Event Schema拡張**: エラー情報の構造化と詳細なトレーサビリティ
2. **エラーリカバリー強化**: 自動リトライ、エラー分類、デッドレターキュー

## 実装された機能

### 1. 拡張Event Schema

新しく追加されたフィールド：

```json
{
  "event_id": "EVT-20251106-123456-abc123",
  "timestamp": "2025-11-06T12:34:56.789",
  "event_type": "action",
  "source": "observer_daemon",
  "data": {},
  
  // 🆕 新規フィールド
  "status": "success",  // pending|success|failed|retrying|dead_letter
  "error_info": {
    "category": "transient",  // transient|permanent|unknown
    "message": "Connection timeout",
    "type": "TimeoutError",
    "stacktrace": "...",
    "context": {}
  },
  "retry_info": {
    "count": 2,
    "max_retries": 3,
    "next_retry_at": "2025-11-06T12:35:00.000",
    "backoff_seconds": 4.0
  },
  "recovery_actions": [
    {
      "timestamp": "2025-11-06T12:34:58.000",
      "action": "exponential_backoff",
      "backoff_seconds": 2.0,
      "event_id": "EVT-..."
    }
  ]
}
```

### 2. エラー分類システム

#### Transient Errors (一時的エラー)
リトライ推奨のエラー：
- `TimeoutError`
- `ConnectionError`, `ConnectionResetError`
- `ConnectionAbortedError`, `ConnectionRefusedError`

#### Permanent Errors (恒久的エラー)
リトライ不要のエラー：
- `ValueError` (入力値の問題)
- `FileNotFoundError` (存在しないリソース)
- `KeyError` (データ構造の問題)
- `TypeError`, `AttributeError`

### 3. 自動リトライメカニズム

- **エクスポネンシャルバックオフ**: 2^n秒の待機時間
- **最大リトライ回数**: デフォルト3回（カスタマイズ可能）
- **デッドレターキュー**: リトライ上限到達時に専用ログに記録

## 使い方

### 基本的な使用法

```python
from utils.resilient_event_stream import get_resilient_stream

stream = get_resilient_stream()

# リトライ機能付きでアクションを実行
def my_action():
    # 何らかの処理
    return {"result": "success"}

event_id = stream.emit_with_retry(
    event_type="action",
    source="my_service",
    action=my_action,
    max_retries=3,
    tags=["important"]
)
```

### エラー管理CLIツール

```bash
# エラー状況の確認
python utils/error_recovery_cli.py status

# デッドレターキューの確認
python utils/error_recovery_cli.py dlq

# 失敗イベント一覧
python utils/error_recovery_cli.py failed

# リトライ候補の確認
python utils/error_recovery_cli.py retry-candidates

# 特定イベントの詳細
python utils/error_recovery_cli.py detail <EVENT_ID>

# エラーレポートのエクスポート
python utils/error_recovery_cli.py export --output error_report.json
```

## マイグレーションガイド

### 既存コードの移行

#### Before (旧ResonantEventStream)
```python
from utils.resonant_event_stream import get_stream

stream = get_stream()
event_id = stream.emit(
    event_type="action",
    source="service",
    data={"key": "value"}
)
```

#### After (新ResilientEventStream)
```python
from utils.resilient_event_stream import get_resilient_stream

stream = get_resilient_stream()

# 通常の記録（エラーなし）
event_id = stream.emit(
    event_type="action",
    source="service",
    data={"key": "value"}
)

# リトライ機能付き記録
def my_operation():
    # 処理内容
    return {"result": "data"}

event_id = stream.emit_with_retry(
    event_type="action",
    source="service",
    action=my_operation,
    max_retries=3
)
```

### 段階的移行戦略

1. **Phase 1: 並行稼働**
   - 既存の`ResonantEventStream`はそのまま維持
   - 新規コードから`ResilientEventStream`を使用開始

2. **Phase 2: 重要パス移行**
   - observer_daemon、webhook_receiverなど重要コンポーネントを移行
   - デッドレターキューの監視を開始

3. **Phase 3: 完全移行**
   - すべてのコンポーネントを新システムに移行
   - 旧イベントログからデータマイグレーション（必要に応じて）

## ファイル構成

```
resonant-engine/
├── utils/
│   ├── resonant_event_stream.py     # 既存のイベントストリーム
│   ├── resilient_event_stream.py    # 🆕 新しいResilientEventStream
│   └── error_recovery_cli.py        # 🆕 エラー管理CLI
├── logs/
│   ├── event_stream.jsonl           # メインイベントストリーム
│   └── dead_letter_queue.jsonl      # 🆕 デッドレターキュー
└── docs/
    └── p0_improvement_guide.md      # このドキュメント
```

## 監視とメンテナンス

### 定期チェック

```bash
# 毎日実行推奨
python utils/error_recovery_cli.py status

# エラーが検出された場合
python utils/error_recovery_cli.py dlq
python utils/error_recovery_cli.py retry-candidates
```

### アラート設定

デッドレターキューに新しいイベントが追加されたら通知を設定することを推奨：

```bash
# 簡易的な監視スクリプト例
watch -n 300 'python utils/error_recovery_cli.py status'
```

## テスト実行

新機能のデモを実行：

```bash
cd /Users/zero/Projects/resonant-engine
python utils/resilient_event_stream.py
```

出力例：
```
=== P0改善デモ: Event Schema拡張 + エラーリカバリー ===

[ケース1] 成功するアクション
[✅ Event Emitted] EVT-...: action (success)

[ケース2] 一時的エラー → リトライで成功
[🔄 Event Emitted] EVT-...: action (retrying)
[🔄 Retry] Attempt 1/3, waiting 2.0s...
[✅ Event Emitted] EVT-...: action (success)

[ケース3] 恒久的エラー → 即座に失敗
[❌ Event Emitted] EVT-...: action (failed)

[ケース4] リトライ上限到達 → デッドレターキュー
[🔄 Event Emitted] EVT-...: action (retrying)
[💀 Event Emitted] EVT-...: action (dead_letter)

=== エラー統計 ===
失敗イベント: 1件
デッドレターキュー: 1件
手動リトライ候補: 1件
```

## トラブルシューティング

### Q: デッドレターキューにイベントが溜まってきた

A: まずエラーカテゴリを確認：
```bash
python utils/error_recovery_cli.py dlq
```

- **Transient errors**: 外部サービスの一時的な問題。手動リトライや問題解決後の再実行を検討
- **Permanent errors**: コードやデータの問題。修正が必要

### Q: リトライ回数をカスタマイズしたい

A: `emit_with_retry()`の`max_retries`パラメータを指定：
```python
stream.emit_with_retry(
    event_type="action",
    source="service",
    action=my_action,
    max_retries=5  # デフォルトは3
)
```

### Q: カスタムエラー分類を追加したい

A: `ResilientEventStream._classify_error()`メソッドを拡張：
```python
def _classify_error(self, error: Exception) -> ErrorCategory:
    # カスタムエラータイプを追加
    if isinstance(error, MyCustomError):
        return ErrorCategory.TRANSIENT
    return super()._classify_error(error)
```

## まとめ

このP0改善により、Resonant Engineは：

✅ **より堅牢**: 自動リトライによる一時的エラーからの回復  
✅ **より観測可能**: 詳細なエラー情報とトレーサビリティ  
✅ **より保守しやすい**: エラー管理CLIによる容易な監視・デバッグ  

になりました。

---

**実装日**: 2025-11-06  
**実装者**: Hiroaki Kato with Claude (Sonnet 4.5)
