"""
リトライ戦略の抽象化

Strategy パターンを使用して、様々なリトライ戦略を実装。
"""

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


class ExponentialBackoffStrategy(RetryStrategy):
    """
    エクスポネンシャルバックオフ戦略
    
    バックオフ時間 = base ^ attempt
    例: base=2 → 1, 2, 4, 8, 16秒...
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


# デモ・テスト用コード
if __name__ == "__main__":
    print("🧪 Retry Strategy Demo")
    print("=" * 60)
    
    strategies = [
        ExponentialBackoffStrategy(base=2.0, jitter_factor=0.0),
        LinearBackoffStrategy(initial_delay=1.0, increment=2.0, jitter_factor=0.0),
        ConstantBackoffStrategy(delay=5.0, jitter_factor=0.0),
        FibonacciBackoffStrategy(unit=1.0, jitter_factor=0.0)
    ]
    
    for strategy in strategies:
        print(f"\n📊 {strategy.get_strategy_name()}")
        print("-" * 60)
        backoffs = [strategy.get_backoff_with_jitter(i) for i in range(10)]
        print(f"Backoffs (0-9): {', '.join(f'{b:.1f}s' for b in backoffs)}")
    
    print("\n" + "=" * 60)
    print("✅ All strategies demonstrated successfully!")

