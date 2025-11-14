# P2改善項目 詳細設計書

**プロジェクト**: Resonant Engine v1.1  
**作成日**: 2025-11-07  
**設計者**: Claude Sonnet 4.5  
**実装者**: Cursor (Claude Sonnet 4.5)  
**ステータス**: 設計完了 / 実装待ち

---

## 📋 目次

1. [概要](#概要)
2. [P2-1: リトライ戦略の抽象化](#p2-1-リトライ戦略の抽象化)
3. [P2-2: CLI出力の視覚化改善](#p2-2-cli出力の視覚化改善)
4. [P2-3: 最大バックオフ時間の制限](#p2-3-最大バックオフ時間の制限)
5. [実装優先順位](#実装優先順位)
6. [テスト方針](#テスト方針)

---

## 概要

### 背景

P1改善項目の実装により、基本的なエラーハンドリングとメトリクス収集基盤が整いました。P2改善項目は、より高度な運用性と保守性を実現するための改善です。

### P2改善項目一覧

| 項目 | 優先度 | 工数見積 | 目的 |
|------|--------|---------|------|
| P2-1: リトライ戦略の抽象化 | 高 | 3-4時間 | 拡張性・保守性向上 |
| P2-2: CLI出力の視覚化改善 | 中 | 2-3時間 | 運用性向上 |
| P2-3: 最大バックオフ時間の制限 | 高 | 30分 | 実用性向上 |

### 実装方針

- **後方互換性**: 既存のAPIは維持
- **段階的移行**: デフォルトは既存動作、オプションで新機能
- **テスト駆動**: 各機能に対してユニットテストを作成

---

## P2-1: リトライ戦略の抽象化

### 目的

現在のリトライ戦略はエクスポネンシャルバックオフに固定されています。Strategy パターンを導入することで、以下を実現します：

1. **拡張性**: 新しいリトライ戦略を簡単に追加
2. **柔軟性**: 状況に応じて戦略を切り替え
3. **保守性**: 戦略ごとのロジックを分離

### 要件定義

#### 機能要件

1. リトライ戦略を抽象化する基底クラス `RetryStrategy` を定義
2. 以下の具象戦略を実装：
   - `ExponentialBackoffStrategy`（既存動作）
   - `LinearBackoffStrategy`（線形バックオフ）
   - `ConstantBackoffStrategy`（固定間隔）
   - `FibonacciBackoffStrategy`（フィボナッチ数列）
3. 戦略は実行時に切り替え可能
4. 各戦略にジッター機能を組み込み

#### 非機能要件

- 既存の `ResilientEventStream` APIは変更しない（デフォルト動作維持）
- パフォーマンスへの影響を最小化
- 各戦略は独立してテスト可能

### アーキテクチャ設計

```
┌─────────────────────────────────┐
│  ResilientEventStream           │
│  - retry_strategy: RetryStrategy│
│  + emit_with_retry()            │
└───────────────┬─────────────────┘
                │ uses
                ▼
┌─────────────────────────────────┐
│  <<abstract>>                   │
│  RetryStrategy                  │
│  + calculate_backoff(attempt)   │
│  + should_retry(attempt, max)   │
│  + apply_jitter(seconds)        │
└───────────────┬─────────────────┘
                │
        ┌───────┴───────┬──────────────┬─────────────┐
        ▼               ▼              ▼             ▼
┌──────────────┐ ┌─────────────┐ ┌──────────┐ ┌──────────┐
│Exponential   │ │Linear       │ │Constant  │ │Fibonacci │
│Backoff       │ │Backoff      │ │Backoff   │ │Backoff   │
│Strategy      │ │Strategy     │ │Strategy  │ │Strategy  │
└──────────────┘ └─────────────┘ └──────────┘ └──────────┘
```

### 詳細設計

#### 1. 基底クラス: `RetryStrategy`

**ファイル**: `utils/retry_strategy.py`（新規作成）

```python
from abc import ABC, abstractmethod
import random
from typing import Optional


class RetryStrategy(ABC):
    """
    リトライ戦略の基底クラス
    
    すべてのリトライ戦略はこのクラスを継承する。
    """
    
    def __init__(self, jitter_factor: float = 0.2, max_backoff: float = 300.0):
        """
        Args:
            jitter_factor: ジッター係数（0.0〜1.0）デフォルト: 0.2 (±20%)
            max_backoff: 最大バックオフ時間（秒）デフォルト: 300秒（5分）
        """
        self.jitter_factor = jitter_factor
        self.max_backoff = max_backoff
    
    @abstractmethod
    def calculate_backoff(self, attempt: int) -> float:
        """
        リトライ試行回数に基づいてバックオフ時間を計算
        
        Args:
            attempt: リトライ試行回数（0始まり）
            
        Returns:
            バックオフ時間（秒）
        """
        pass
    
    def get_backoff_with_jitter(self, attempt: int) -> float:
        """
        ジッター適用済みのバックオフ時間を取得
        
        Args:
            attempt: リトライ試行回数（0始まり）
            
        Returns:
            ジッター適用済みバックオフ時間（秒）
        """
        backoff = self.calculate_backoff(attempt)
        backoff = self._apply_jitter(backoff)
        backoff = min(backoff, self.max_backoff)
        return backoff
    
    def _apply_jitter(self, backoff_seconds: float) -> float:
        """
        ジッターを適用
        
        Args:
            backoff_seconds: 元のバックオフ時間
            
        Returns:
            ジッター適用後のバックオフ時間
        """
        if self.jitter_factor <= 0:
            return backoff_seconds
        
        jitter_range = backoff_seconds * self.jitter_factor
        jitter = random.uniform(-jitter_range, jitter_range)
        return max(0.0, backoff_seconds + jitter)
    
    def should_retry(self, attempt: int, max_retries: int) -> bool:
        """
        リトライを続けるべきか判定
        
        Args:
            attempt: 現在の試行回数（0始まり）
            max_retries: 最大リトライ回数
            
        Returns:
            リトライを続ける場合True
        """
        return attempt < max_retries
    
    def get_strategy_name(self) -> str:
        """戦略名を取得"""
        return self.__class__.__name__
```

#### 2. 具象戦略クラス

**ファイル**: `utils/retry_strategy.py`（同じファイルに追加）

```python
class ExponentialBackoffStrategy(RetryStrategy):
    """
    エクスポネンシャルバックオフ戦略
    
    バックオフ時間 = base ^ attempt
    例: base=2 → 2, 4, 8, 16, 32秒...
    """
    
    def __init__(self, base: float = 2.0, **kwargs):
        """
        Args:
            base: 指数の基数（デフォルト: 2.0）
            **kwargs: 親クラスへの引数（jitter_factor, max_backoff）
        """
        super().__init__(**kwargs)
        self.base = base
    
    def calculate_backoff(self, attempt: int) -> float:
        return self.base ** attempt


class LinearBackoffStrategy(RetryStrategy):
    """
    線形バックオフ戦略
    
    バックオフ時間 = initial_delay + (increment * attempt)
    例: initial=1, increment=2 → 1, 3, 5, 7, 9秒...
    """
    
    def __init__(self, initial_delay: float = 1.0, increment: float = 2.0, **kwargs):
        """
        Args:
            initial_delay: 初回遅延時間（秒）
            increment: 増分時間（秒）
            **kwargs: 親クラスへの引数
        """
        super().__init__(**kwargs)
        self.initial_delay = initial_delay
        self.increment = increment
    
    def calculate_backoff(self, attempt: int) -> float:
        return self.initial_delay + (self.increment * attempt)


class ConstantBackoffStrategy(RetryStrategy):
    """
    固定間隔バックオフ戦略
    
    バックオフ時間 = delay（常に一定）
    例: delay=5 → 5, 5, 5, 5, 5秒...
    """
    
    def __init__(self, delay: float = 5.0, **kwargs):
        """
        Args:
            delay: 固定遅延時間（秒）
            **kwargs: 親クラスへの引数
        """
        super().__init__(**kwargs)
        self.delay = delay
    
    def calculate_backoff(self, attempt: int) -> float:
        return self.delay


class FibonacciBackoffStrategy(RetryStrategy):
    """
    フィボナッチバックオフ戦略
    
    バックオフ時間 = fibonacci(attempt) * unit
    例: unit=1 → 1, 1, 2, 3, 5, 8, 13秒...
    """
    
    def __init__(self, unit: float = 1.0, **kwargs):
        """
        Args:
            unit: フィボナッチ数に掛ける単位時間（秒）
            **kwargs: 親クラスへの引数
        """
        super().__init__(**kwargs)
        self.unit = unit
        self._fib_cache = {0: 1, 1: 1}
    
    def _fibonacci(self, n: int) -> int:
        """フィボナッチ数を計算（キャッシュ付き）"""
        if n in self._fib_cache:
            return self._fib_cache[n]
        
        self._fib_cache[n] = self._fibonacci(n - 1) + self._fibonacci(n - 2)
        return self._fib_cache[n]
    
    def calculate_backoff(self, attempt: int) -> float:
        return self._fibonacci(attempt) * self.unit
```

#### 3. `ResilientEventStream` の修正

**ファイル**: `utils/resilient_event_stream.py`

**変更点**:

```python
# インポート追加
from utils.retry_strategy import RetryStrategy, ExponentialBackoffStrategy

class ResilientEventStream:
    def __init__(self, 
                 stream_path: Path = None,
                 dead_letter_path: Path = None,
                 max_retries: int = 3,
                 retry_backoff_base: float = 2.0,  # 後方互換性のため残す
                 enable_metrics: bool = True,
                 retry_strategy: Optional[RetryStrategy] = None):  # 新規追加
        """
        Args:
            retry_strategy: リトライ戦略（Noneの場合はExponentialBackoff）
        """
        # ... 既存コード ...
        
        # リトライ戦略の初期化
        if retry_strategy is None:
            # デフォルトはExponentialBackoff（既存動作を維持）
            self.retry_strategy = ExponentialBackoffStrategy(
                base=retry_backoff_base,
                max_backoff=300.0
            )
        else:
            self.retry_strategy = retry_strategy
    
    def emit_with_retry(self, ...):
        # ... 既存コード ...
        
        # リトライ可能な場合
        if retry_count < max_retries:
            # 戦略を使ってバックオフ時間を計算
            backoff_seconds = self.retry_strategy.get_backoff_with_jitter(retry_count)
            
            # ... 既存コード（ジッター計算は削除）...
```

### 実装手順

1. `utils/retry_strategy.py` を新規作成
   - `RetryStrategy` 基底クラス
   - 4つの具象戦略クラス

2. `utils/resilient_event_stream.py` を修正
   - インポート追加
   - `__init__` に `retry_strategy` パラメータ追加
   - `emit_with_retry` のバックオフ計算をリファクタリング

3. ユニットテスト作成（`tests/test_retry_strategy.py`）

### テストケース

```python
# tests/test_retry_strategy.py

def test_exponential_backoff():
    strategy = ExponentialBackoffStrategy(base=2.0, jitter_factor=0.0)
    assert strategy.calculate_backoff(0) == 1
    assert strategy.calculate_backoff(1) == 2
    assert strategy.calculate_backoff(2) == 4
    assert strategy.calculate_backoff(3) == 8

def test_linear_backoff():
    strategy = LinearBackoffStrategy(initial_delay=1.0, increment=2.0, jitter_factor=0.0)
    assert strategy.calculate_backoff(0) == 1.0
    assert strategy.calculate_backoff(1) == 3.0
    assert strategy.calculate_backoff(2) == 5.0

def test_max_backoff_limit():
    strategy = ExponentialBackoffStrategy(base=2.0, max_backoff=10.0, jitter_factor=0.0)
    # 2^10 = 1024だが、max_backoffで10秒に制限される
    backoff = strategy.get_backoff_with_jitter(10)
    assert backoff <= 10.0

def test_jitter_application():
    strategy = ExponentialBackoffStrategy(base=2.0, jitter_factor=0.2)
    # ジッターがあるため、正確な値ではなく範囲でテスト
    backoff = strategy.get_backoff_with_jitter(2)
    expected = 4.0
    assert expected * 0.8 <= backoff <= expected * 1.2
```

---

## P2-2: CLI出力の視覚化改善

### 目的

現在のCLI出力はプレーンテキストで可読性が低いです。`rich` ライブラリを導入して視覚的に改善します。

### 要件定義

#### 機能要件

1. `rich` ライブラリを使った表形式表示
2. カラーコーディング（成功=緑、エラー=赤、警告=黄）
3. プログレスバー（大量データ処理時）
4. Markdown形式のヘルプ表示
5. 既存出力との互換性（`--plain` オプション）

#### 非機能要件

- `rich` が利用不可の環境でも動作（フォールバック）
- パフォーマンス劣化なし

### アーキテクチャ設計

```
┌─────────────────────────────────┐
│  ErrorRecoveryCLI               │
│  - use_rich: bool               │
│  + show_status()                │
│  + list_dead_letter_queue()     │
└───────────────┬─────────────────┘
                │
        ┌───────┴───────┐
        ▼               ▼
┌──────────────┐ ┌─────────────┐
│RichFormatter │ │PlainFormatter│
│(rich使用)    │ │(既存動作)   │
└──────────────┘ └─────────────┘
```

### 詳細設計

#### 1. Rich フォーマッターの追加

**ファイル**: `utils/error_recovery_cli.py`（修正）

```python
# インポート追加
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

class ErrorRecoveryCLI:
    def __init__(self, use_rich: bool = True):
        self.stream = ResilientEventStream()
        self.metrics = get_metrics_collector()
        self.use_rich = use_rich and RICH_AVAILABLE
        
        if self.use_rich:
            self.console = Console()
    
    def show_status(self):
        """エラー状況の概要を表示"""
        failed = self.stream.get_failed_events()
        dlq = self.stream.get_dead_letter_queue()
        retry_candidates = self.stream.get_retry_candidates()
        
        if self.use_rich:
            self._show_status_rich(failed, dlq, retry_candidates)
        else:
            self._show_status_plain(failed, dlq, retry_candidates)
    
    def _show_status_rich(self, failed, dlq, retry_candidates):
        """Rich形式でステータス表示"""
        # パネル作成
        title = Panel.fit(
            "📊 Resonant Engine - Error Recovery Status",
            border_style="bold blue"
        )
        self.console.print(title)
        self.console.print()
        
        # 統計テーブル
        table = Table(title="Error Statistics", box=box.ROUNDED)
        table.add_column("Type", style="cyan", no_wrap=True)
        table.add_column("Count", justify="right", style="magenta")
        table.add_column("Status", justify="center")
        
        table.add_row("Failed Events", str(len(failed)), "❌")
        table.add_row("Dead Letter Queue", str(len(dlq)), "💀")
        table.add_row("Retry Candidates", str(len(retry_candidates)), "🔄")
        
        self.console.print(table)
        self.console.print()
        
        if not dlq and not failed:
            self.console.print("✅ [bold green]No errors detected - system is healthy![/bold green]")
            return
        
        # エラーカテゴリ別集計
        error_by_category = {}
        for event in dlq + failed:
            error_info = event.get("error_info", {})
            category = error_info.get("category", "unknown")
            error_by_category[category] = error_by_category.get(category, 0) + 1
        
        if error_by_category:
            cat_table = Table(title="Error Breakdown", box=box.SIMPLE)
            cat_table.add_column("Category", style="yellow")
            cat_table.add_column("Count", justify="right", style="cyan")
            
            for category, count in error_by_category.items():
                emoji = "⚡" if category == "transient" else "🚫" if category == "permanent" else "❓"
                cat_table.add_row(f"{emoji} {category}", str(count))
            
            self.console.print(cat_table)
    
    def _show_status_plain(self, failed, dlq, retry_candidates):
        """既存のプレーン形式でステータス表示"""
        # 既存コードをそのまま使用
        print("=" * 60)
        print("📊 Resonant Engine - Error Recovery Status")
        # ... 既存コード ...
    
    def list_dead_letter_queue(self, limit: int = 20):
        """デッドレターキューを一覧表示"""
        dlq_events = self.stream.get_dead_letter_queue(limit=limit)
        
        if not dlq_events:
            if self.use_rich:
                self.console.print("✅ [bold green]Dead letter queue is empty![/bold green]")
            else:
                print("✅ Dead letter queue is empty!")
            return
        
        if self.use_rich:
            self._list_dlq_rich(dlq_events)
        else:
            self._list_dlq_plain(dlq_events)
    
    def _list_dlq_rich(self, dlq_events):
        """Rich形式でDLQ一覧表示"""
        table = Table(title="💀 Dead Letter Queue", box=box.ROUNDED)
        table.add_column("#", justify="right", style="cyan", no_wrap=True)
        table.add_column("Event ID", style="magenta")
        table.add_column("Timestamp", style="green")
        table.add_column("Error", style="red")
        table.add_column("Category", justify="center")
        table.add_column("Retries", justify="right")
        
        for i, event in enumerate(dlq_events, 1):
            error_info = event.get("error_info", {})
            retry_info = event.get("retry_info", {})
            
            category = error_info.get("category", "unknown")
            emoji = "⚡" if category == "transient" else "🚫"
            
            table.add_row(
                str(i),
                event['event_id'][:20] + "...",
                event['timestamp'][:19],
                error_info.get('message', 'N/A')[:30] + "...",
                f"{emoji} {category}",
                f"{retry_info.get('count', 0)}/{retry_info.get('max_retries', 0)}"
            )
        
        self.console.print(table)
    
    def _list_dlq_plain(self, dlq_events):
        """既存のプレーン形式でDLQ表示"""
        # 既存コードを使用
        print("=" * 60)
        print("💀 Dead Letter Queue")
        # ... 既存コード ...
```

#### 2. コマンドライン引数の追加

```python
def main():
    parser = argparse.ArgumentParser(
        description="Error Recovery CLI - Manage failed events and dead letter queue"
    )
    
    # グローバルオプション
    parser.add_argument("--plain", action="store_true", help="Use plain text output (disable rich formatting)")
    
    # ... 既存のサブコマンド定義 ...
    
    args = parser.parse_args()
    
    # use_rich = not args.plain
    cli = ErrorRecoveryCLI(use_rich=not args.plain)
    
    # ... 既存のコマンド処理 ...
```

### 実装手順

1. `rich` を依存関係に追加（`requirements.txt` または `pyproject.toml`）
2. `utils/error_recovery_cli.py` を修正
   - Richインポート追加（try-except）
   - `__init__` に `use_rich` パラメータ
   - 各表示メソッドを Rich版とPlain版に分離
3. テスト実行

### 使用例

```bash
# Rich形式（デフォルト）
python utils/error_recovery_cli.py status

# プレーンテキスト形式
python utils/error_recovery_cli.py status --plain
```

---

## P2-3: 最大バックオフ時間の制限

### 目的

現在、エクスポネンシャルバックオフには上限がないため、理論上は無限に待機時間が増加します。実用上は5分（300秒）を上限とします。

### 要件定義

#### 機能要件

1. すべてのリトライ戦略に `max_backoff` パラメータを追加
2. デフォルト値: 300秒（5分）
3. 設定可能（柔軟性を確保）

#### 非機能要件

- 既存動作への影響を最小化
- パフォーマンスへの影響なし

### 詳細設計

**実装箇所**: 
- `utils/retry_strategy.py` の `RetryStrategy.__init__`（既に設計済み）
- `utils/resilient_event_stream.py` の戦略初期化

```python
# ResilientEventStream.__init__ の修正
if retry_strategy is None:
    self.retry_strategy = ExponentialBackoffStrategy(
        base=retry_backoff_base,
        max_backoff=300.0  # 5分上限
    )
else:
    self.retry_strategy = retry_strategy
```

### 実装手順

1. `RetryStrategy` 基底クラスに `max_backoff` パラメータ追加（**既に設計済み**）
2. `get_backoff_with_jitter` メソッドで上限を適用（**既に設計済み**）
3. `ResilientEventStream` のデフォルト戦略に `max_backoff=300.0` を設定

### テストケース

```python
def test_max_backoff_enforcement():
    """最大バックオフ時間が正しく適用されるか"""
    strategy = ExponentialBackoffStrategy(base=2.0, max_backoff=10.0, jitter_factor=0.0)
    
    # 2^10 = 1024秒だが、10秒に制限される
    backoff = strategy.get_backoff_with_jitter(10)
    assert backoff == 10.0
    
    # より大きな試行回数でもmax_backoffを超えない
    backoff = strategy.get_backoff_with_jitter(20)
    assert backoff == 10.0

def test_configurable_max_backoff():
    """max_backoffが設定可能か"""
    strategy = ExponentialBackoffStrategy(base=2.0, max_backoff=60.0, jitter_factor=0.0)
    
    backoff = strategy.get_backoff_with_jitter(10)
    assert backoff == 60.0
```

---

## 実装優先順位

### 推奨実装順序

1. **P2-3: 最大バックオフ時間の制限** （30分）
   - 最も簡単で影響範囲が明確
   - P2-1の前提条件（`RetryStrategy`設計に含まれる）

2. **P2-1: リトライ戦略の抽象化** （3-4時間）
   - アーキテクチャの大きな変更
   - テストが重要

3. **P2-2: CLI出力の視覚化改善** （2-3時間）
   - 独立した改善
   - オプショナル（`--plain`でフォールバック）

### 段階的実装アプローチ

#### Stage 1: P2-3（最小リスク）
- `RetryStrategy` の設計に `max_backoff` は既に含まれている
- 実装は設計通りに進める

#### Stage 2: P2-1（コア機能）
1. `utils/retry_strategy.py` 作成
2. ユニットテスト作成
3. `ResilientEventStream` 統合
4. 既存テストが通ることを確認

#### Stage 3: P2-2（UI改善）
1. `rich` インストール
2. Rich版メソッド実装
3. `--plain` オプション追加
4. 両方の出力形式をテスト

---

## テスト方針

### ユニットテスト

**ファイル**: `tests/test_retry_strategy.py`（新規作成）

```python
import pytest
from utils.retry_strategy import (
    ExponentialBackoffStrategy,
    LinearBackoffStrategy,
    ConstantBackoffStrategy,
    FibonacciBackoffStrategy
)

class TestExponentialBackoff:
    def test_calculate_backoff(self):
        strategy = ExponentialBackoffStrategy(base=2.0, jitter_factor=0.0)
        assert strategy.calculate_backoff(0) == 1
        assert strategy.calculate_backoff(1) == 2
        assert strategy.calculate_backoff(2) == 4
    
    def test_max_backoff(self):
        strategy = ExponentialBackoffStrategy(base=2.0, max_backoff=10.0, jitter_factor=0.0)
        backoff = strategy.get_backoff_with_jitter(10)
        assert backoff == 10.0

class TestLinearBackoff:
    def test_calculate_backoff(self):
        strategy = LinearBackoffStrategy(initial_delay=1.0, increment=2.0, jitter_factor=0.0)
        assert strategy.calculate_backoff(0) == 1.0
        assert strategy.calculate_backoff(1) == 3.0
        assert strategy.calculate_backoff(2) == 5.0

class TestConstantBackoff:
    def test_calculate_backoff(self):
        strategy = ConstantBackoffStrategy(delay=5.0, jitter_factor=0.0)
        assert strategy.calculate_backoff(0) == 5.0
        assert strategy.calculate_backoff(10) == 5.0

class TestFibonacciBackoff:
    def test_calculate_backoff(self):
        strategy = FibonacciBackoffStrategy(unit=1.0, jitter_factor=0.0)
        assert strategy.calculate_backoff(0) == 1
        assert strategy.calculate_backoff(1) == 1
        assert strategy.calculate_backoff(2) == 2
        assert strategy.calculate_backoff(3) == 3
        assert strategy.calculate_backoff(4) == 5
```

### 統合テスト

**ファイル**: `tests/test_resilient_stream_with_strategies.py`（新規作成）

```python
import pytest
from utils.resilient_event_stream import ResilientEventStream
from utils.retry_strategy import LinearBackoffStrategy

def test_custom_retry_strategy():
    """カスタムリトライ戦略が正しく動作するか"""
    strategy = LinearBackoffStrategy(initial_delay=1.0, increment=1.0, jitter_factor=0.0)
    stream = ResilientEventStream(retry_strategy=strategy, max_retries=2)
    
    attempt_count = {"count": 0}
    
    def failing_action():
        attempt_count["count"] += 1
        if attempt_count["count"] < 3:
            raise ConnectionError("Test error")
        return {"result": "success"}
    
    event_id = stream.emit_with_retry(
        event_type="test",
        source="test",
        action=failing_action
    )
    
    assert attempt_count["count"] == 3
    # 検証: LinearBackoff（1秒、2秒）が使われたか
```

### CLI テスト

```bash
# Rich出力のテスト
python utils/error_recovery_cli.py status
python utils/error_recovery_cli.py dlq

# プレーン出力のテスト
python utils/error_recovery_cli.py status --plain
python utils/error_recovery_cli.py dlq --plain

# 出力の比較
diff <(python utils/error_recovery_cli.py status --plain) <(python utils/error_recovery_cli.py status)
```

---

## 実装チェックリスト

### P2-1: リトライ戦略の抽象化

- [ ] `utils/retry_strategy.py` 作成
  - [ ] `RetryStrategy` 基底クラス
  - [ ] `ExponentialBackoffStrategy`
  - [ ] `LinearBackoffStrategy`
  - [ ] `ConstantBackoffStrategy`
  - [ ] `FibonacciBackoffStrategy`
- [ ] `utils/resilient_event_stream.py` 修正
  - [ ] インポート追加
  - [ ] `retry_strategy` パラメータ追加
  - [ ] バックオフ計算のリファクタリング
- [ ] `tests/test_retry_strategy.py` 作成
  - [ ] 各戦略のユニットテスト
  - [ ] ジッターのテスト
  - [ ] max_backoffのテスト
- [ ] 統合テスト実行
  - [ ] 既存テストがパスするか確認
  - [ ] 新規統合テスト実行

### P2-2: CLI出力の視覚化改善

- [ ] `requirements.txt` に `rich` 追加
- [ ] `utils/error_recovery_cli.py` 修正
  - [ ] Richインポート（try-except）
  - [ ] `use_rich` パラメータ追加
  - [ ] `show_status` のRich版実装
  - [ ] `list_dead_letter_queue` のRich版実装
  - [ ] `list_failed_events` のRich版実装
  - [ ] `show_metrics` のRich版実装（オプション）
  - [ ] `--plain` オプション追加
- [ ] 動作確認
  - [ ] Rich出力の確認
  - [ ] プレーン出力の確認
  - [ ] `rich`未インストール環境での動作確認

### P2-3: 最大バックオフ時間の制限

- [ ] `RetryStrategy.__init__` に `max_backoff` 追加（**設計に含まれる**）
- [ ] `get_backoff_with_jitter` で上限適用（**設計に含まれる**）
- [ ] `ResilientEventStream` のデフォルト値設定
- [ ] テスト作成・実行

---

## 完了条件

### P2-1

- [ ] すべてのユニットテストがパス
- [ ] 既存の `ResilientEventStream` テストがパス
- [ ] 各戦略の動作確認（デモスクリプト実行）
- [ ] ドキュメント更新（README）

### P2-2

- [ ] Rich出力が正常に表示される
- [ ] `--plain` で既存出力が得られる
- [ ] `rich`がない環境でフォールバック動作
- [ ] パフォーマンステスト（大量データ）

### P2-3

- [ ] max_backoffが正しく適用される
- [ ] 既存動作に影響がない
- [ ] テストがパス

---

## 参考資料

### リトライ戦略の比較

| 戦略 | 用途 | 特徴 | 例（秒） |
|------|------|------|---------|
| Exponential | 一般的 | 急激に増加 | 1, 2, 4, 8, 16 |
| Linear | 安定重視 | 緩やかに増加 | 1, 3, 5, 7, 9 |
| Constant | シンプル | 常に一定 | 5, 5, 5, 5, 5 |
| Fibonacci | バランス | 自然な増加 | 1, 1, 2, 3, 5, 8 |

### Rich ライブラリの主要機能

- `Table`: 表形式表示
- `Panel`: 囲み枠付きテキスト
- `Progress`: プログレスバー
- `Console`: カラー出力
- `Syntax`: シンタックスハイライト

---

## 付録: 実装例

### リトライ戦略の使用例

```python
from utils.resilient_event_stream import ResilientEventStream
from utils.retry_strategy import LinearBackoffStrategy, FibonacciBackoffStrategy

# 線形バックオフを使用
linear_strategy = LinearBackoffStrategy(
    initial_delay=1.0,
    increment=2.0,
    max_backoff=60.0
)
stream = ResilientEventStream(retry_strategy=linear_strategy)

# フィボナッチバックオフを使用
fib_strategy = FibonacciBackoffStrategy(
    unit=1.0,
    max_backoff=120.0
)
stream = ResilientEventStream(retry_strategy=fib_strategy)

# デフォルト（Exponential）
stream = ResilientEventStream()  # 既存動作を維持
```

---

**以上、P2改善項目の詳細設計書でした。**

**実装者（Cursor）への指示**:
1. この設計書に従って実装してください
2. 優先順位: P2-3 → P2-1 → P2-2
3. 各項目完了後にテストを実行してください
4. 不明点があれば設計者（Claude）に質問してください

**作成者**: Claude Sonnet 4.5  
**作成日時**: 2025-11-07 17:25:00  
**バージョン**: 1.0
