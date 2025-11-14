# P2改善項目 実装指示書（カーサー向け）

**実装者**: Cursor (Claude Sonnet 4.5)  
**設計者**: Claude Sonnet 4.5  
**作成日**: 2025-11-07  
**プロジェクト**: Resonant Engine v1.1

---

## 📋 作業概要

P2改善項目（推奨・運用改善）の実装を行います。

**詳細設計書**: `docs/p2_improvement_design_spec.md`（必読）

---

## 🎯 実装項目

| 項目 | 優先順位 | 工数 | 説明 |
|------|---------|------|------|
| P2-3 | 最優先★★★ | 30分 | 最大バックオフ時間の制限 |
| P2-1 | 高★★ | 3-4時間 | リトライ戦略の抽象化 |
| P2-2 | 中★ | 2-3時間 | CLI出力の視覚化改善 |

---

## 📝 実装順序

### ステップ1: P2-3（30分）- 最優先

最もシンプルで、P2-1の前提条件です。

**作業内容**:
1. 設計書の「P2-3: 最大バックオフ時間の制限」セクションを読む
2. 実装は主にP2-1の`RetryStrategy`基底クラスに含まれる
3. P2-1と一緒に実装することを推奨

**成果物**: なし（P2-1に統合）

---

### ステップ2: P2-1（3-4時間）- 高優先度

Strategy パターンによるリトライ戦略の抽象化。

#### 2.1 新規ファイル作成

**ファイル**: `utils/retry_strategy.py`

**実装内容**:
1. `RetryStrategy` 基底クラス
   - `__init__(jitter_factor, max_backoff)`
   - `calculate_backoff(attempt)` - 抽象メソッド
   - `get_backoff_with_jitter(attempt)` - ジッター適用
   - `_apply_jitter(backoff_seconds)` - ジッター計算
   - `should_retry(attempt, max_retries)` - リトライ判定
   - `get_strategy_name()` - 戦略名取得

2. 具象戦略クラス（4つ）
   - `ExponentialBackoffStrategy` - 既存動作（base=2.0）
   - `LinearBackoffStrategy` - 線形増加
   - `ConstantBackoffStrategy` - 固定間隔
   - `FibonacciBackoffStrategy` - フィボナッチ数列

**コード**: 設計書の「詳細設計」セクションに完全なコード例あり

#### 2.2 既存ファイル修正

**ファイル**: `utils/resilient_event_stream.py`

**変更箇所**:
1. インポート追加
   ```python
   from utils.retry_strategy import RetryStrategy, ExponentialBackoffStrategy
   ```

2. `__init__` メソッド
   - `retry_strategy: Optional[RetryStrategy] = None` パラメータ追加
   - デフォルト戦略の初期化（`ExponentialBackoffStrategy`）
   ```python
   if retry_strategy is None:
       self.retry_strategy = ExponentialBackoffStrategy(
           base=retry_backoff_base,
           max_backoff=300.0  # 5分上限
       )
   else:
       self.retry_strategy = retry_strategy
   ```

3. `emit_with_retry` メソッド
   - バックオフ計算部分を修正
   ```python
   # 旧コード（削除）
   backoff_seconds = self.retry_backoff_base ** retry_count
   jitter = random.uniform(0.8, 1.2)
   backoff_seconds *= jitter
   
   # 新コード
   backoff_seconds = self.retry_strategy.get_backoff_with_jitter(retry_count)
   ```

#### 2.3 テスト作成

**ファイル**: `tests/test_retry_strategy.py`（新規作成）

**テスト内容**:
- 各戦略のバックオフ計算テスト
- ジッター適用テスト
- max_backoff制限テスト
- リトライ判定テスト

**コード**: 設計書の「テスト方針」セクションに完全なテストコード例あり

#### 2.4 動作確認

```bash
# ユニットテスト実行
cd /Users/zero/Projects/resonant-engine
source venv/bin/activate
python -m pytest tests/test_retry_strategy.py -v

# 既存テストがパスすることを確認
python utils/resilient_event_stream.py

# カスタム戦略のデモ（オプション）
python -c "
from utils.resilient_event_stream import ResilientEventStream
from utils.retry_strategy import LinearBackoffStrategy

strategy = LinearBackoffStrategy(initial_delay=1.0, increment=2.0)
stream = ResilientEventStream(retry_strategy=strategy, max_retries=2)
print('✅ Custom strategy loaded successfully')
"
```

---

### ステップ3: P2-2（2-3時間）- 中優先度

Rich ライブラリによるCLI出力の視覚化。

#### 3.1 依存関係の追加

**ファイル**: `requirements.txt`

```bash
# rich を追加
echo "rich>=13.0.0" >> requirements.txt
pip install rich
```

#### 3.2 既存ファイル修正

**ファイル**: `utils/error_recovery_cli.py`

**変更箇所**:

1. インポート追加（try-except で囲む）
   ```python
   try:
       from rich.console import Console
       from rich.table import Table
       from rich.panel import Panel
       from rich.progress import Progress
       from rich import box
       RICH_AVAILABLE = True
   except ImportError:
       RICH_AVAILABLE = False
   ```

2. `ErrorRecoveryCLI.__init__` 修正
   ```python
   def __init__(self, use_rich: bool = True):
       self.stream = ResilientEventStream()
       self.metrics = get_metrics_collector()
       self.use_rich = use_rich and RICH_AVAILABLE
       
       if self.use_rich:
           self.console = Console()
   ```

3. 各表示メソッドを2つに分割
   - `show_status()` → `_show_status_rich()` + `_show_status_plain()`
   - `list_dead_letter_queue()` → `_list_dlq_rich()` + `_list_dlq_plain()`
   - `list_failed_events()` → `_list_failed_rich()` + `_list_failed_plain()`
   - `show_metrics()` → `_show_metrics_rich()` + `_show_metrics_plain()`（オプション）

4. `main()` 関数の修正
   ```python
   parser.add_argument("--plain", action="store_true", 
                      help="Use plain text output (disable rich formatting)")
   
   # ...
   
   cli = ErrorRecoveryCLI(use_rich=not args.plain)
   ```

**コード**: 設計書の「詳細設計」セクションに完全なコード例あり

#### 3.3 動作確認

```bash
# Rich形式（デフォルト）
python utils/error_recovery_cli.py status
python utils/error_recovery_cli.py dlq
python utils/error_recovery_cli.py metrics

# プレーン形式
python utils/error_recovery_cli.py status --plain
python utils/error_recovery_cli.py dlq --plain

# richがない環境でのテスト（オプション）
pip uninstall rich -y
python utils/error_recovery_cli.py status  # フォールバックを確認
pip install rich  # 再インストール
```

---

## ✅ 完了チェックリスト

### P2-1: リトライ戦略の抽象化

- [ ] `utils/retry_strategy.py` 作成完了
  - [ ] `RetryStrategy` 基底クラス
  - [ ] 4つの具象戦略クラス
- [ ] `utils/resilient_event_stream.py` 修正完了
  - [ ] インポート追加
  - [ ] `retry_strategy` パラメータ追加
  - [ ] バックオフ計算のリファクタリング
- [ ] `tests/test_retry_strategy.py` 作成完了
- [ ] すべてのテストがパス
- [ ] 既存のデモスクリプトが正常動作

### P2-2: CLI出力の視覚化改善

- [ ] `requirements.txt` に `rich` 追加
- [ ] `pip install rich` 実行
- [ ] `utils/error_recovery_cli.py` 修正完了
  - [ ] Rich インポート（try-except）
  - [ ] `use_rich` パラメータ追加
  - [ ] Rich版メソッド実装
  - [ ] Plain版メソッド保持
  - [ ] `--plain` オプション追加
- [ ] Rich形式の出力確認
- [ ] プレーン形式の出力確認
- [ ] フォールバック動作確認

### P2-3: 最大バックオフ時間の制限

- [ ] P2-1の実装に含まれる（`max_backoff=300.0`）
- [ ] テストで上限が効いていることを確認

---

## 🔍 テスト方法

### ユニットテスト

```bash
# 全テスト実行
python -m pytest tests/ -v

# P2-1のテストのみ
python -m pytest tests/test_retry_strategy.py -v

# カバレッジ確認（オプション）
python -m pytest tests/test_retry_strategy.py --cov=utils.retry_strategy --cov-report=html
```

### 統合テスト

```bash
# ResilientEventStream のデモ
python utils/resilient_event_stream.py

# CLI のテスト
python utils/error_recovery_cli.py status
python utils/error_recovery_cli.py dlq
python utils/error_recovery_cli.py metrics
python utils/error_recovery_cli.py prometheus --output test.prom
```

---

## 📊 完了報告

すべての実装とテストが完了したら、以下を作成してください：

**ファイル**: `docs/p2_improvement_completion_report.md`

**内容**:
- 実装概要
- 変更したファイル一覧
- テスト結果
- 動作確認のスクリーンショット（オプション）
- 既知の問題（あれば）

**テンプレート**: `docs/p1_improvement_completion_report.md` を参考

---

## 🚨 注意事項

### 後方互換性の維持

- `ResilientEventStream` の既存APIは変更しない
- `retry_strategy` パラメータは `Optional`（デフォルト: None）
- デフォルト動作は既存と同じ（`ExponentialBackoffStrategy`）

### エラーハンドリング

- `rich` のインポートは try-except で囲む
- `RICH_AVAILABLE = False` の場合はプレーン出力にフォールバック
- テスト実行時は `rich` が利用可能な前提

### コードスタイル

- 既存コードのスタイルに合わせる
- docstring は Google Style
- 型ヒントを使用

---

## ❓ 質問・問題が発生した場合

### 設計について

設計書（`docs/p2_improvement_design_spec.md`）を確認してください。
不明点がある場合は設計者（Claude）に質問してください。

### 実装について

以下のファイルを参考にしてください：
- 既存の実装: `utils/resilient_event_stream.py`
- P1の完了報告: `docs/p1_improvement_completion_report.md`
- エラーハンドリング: `utils/error_recovery.py`

### テストについ��

既存のテストファイルを参考にしてください：
- 統合テスト例: `utils/resilient_event_stream.py` の `if __name__ == "__main__"` 部分

---

## 📝 Gitコミット

各ステップ完了後にコミットしてください：

```bash
# P2-1 完了後
git add utils/retry_strategy.py utils/resilient_event_stream.py tests/test_retry_strategy.py
git commit -m "feat: P2-1 リトライ戦略の抽象化

- Strategy パターン導入
- 4つの具象戦略実装（Exponential/Linear/Constant/Fibonacci）
- 最大バックオフ時間の制限（300秒）
- ユニットテスト追加"

# P2-2 完了後
git add requirements.txt utils/error_recovery_cli.py
git commit -m "feat: P2-2 CLI出力の視覚化改善

- Rich ライブラリ導入
- 表形式・カラー出力対応
- --plain オプションでフォールバック
- 既存動作を維持"

# 完了報告書作成後
git add docs/p2_improvement_completion_report.md
git commit -m "docs: P2改善項目の完了報告書"

# プッシュ
git push origin main
```

---

## 🎯 成功の定義

以下がすべて満たされたら成功です：

1. ✅ すべてのユニットテストがパス
2. ✅ 既存のデモスクリプトが正常動作
3. ✅ Rich形式とプレーン形式の両方が動作
4. ✅ 後方互換性が保たれている
5. ✅ 完了報告書が作成されている
6. ✅ Gitコミット・プッシュ完了

---

**実装頑張ってください！**

**設計者**: Claude Sonnet 4.5  
**作成日時**: 2025-11-07 17:35:00  
**バージョン**: 1.0
