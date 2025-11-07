"""
リトライ戦略のユニットテスト
"""

import pytest
from utils.retry_strategy import (
    RetryStrategy,
    ExponentialBackoffStrategy,
    LinearBackoffStrategy,
    ConstantBackoffStrategy,
    FibonacciBackoffStrategy
)


class TestExponentialBackoff:
    """エクスポネンシャルバックオフ戦略のテスト"""
    
    def test_calculate_backoff_base2(self):
        """基数2でのバックオフ計算"""
        strategy = ExponentialBackoffStrategy(base=2.0, jitter_factor=0.0)
        assert strategy.calculate_backoff(0) == 1
        assert strategy.calculate_backoff(1) == 2
        assert strategy.calculate_backoff(2) == 4
        assert strategy.calculate_backoff(3) == 8
        assert strategy.calculate_backoff(4) == 16
    
    def test_calculate_backoff_base3(self):
        """基数3でのバックオフ計算"""
        strategy = ExponentialBackoffStrategy(base=3.0, jitter_factor=0.0)
        assert strategy.calculate_backoff(0) == 1
        assert strategy.calculate_backoff(1) == 3
        assert strategy.calculate_backoff(2) == 9
        assert strategy.calculate_backoff(3) == 27
    
    def test_max_backoff_limit(self):
        """最大バックオフ時間が正しく適用されるか"""
        strategy = ExponentialBackoffStrategy(base=2.0, max_backoff=10.0, jitter_factor=0.0)
        # 2^10 = 1024だが、max_backoffで10秒に制限される
        backoff = strategy.get_backoff_with_jitter(10)
        assert backoff == 10.0
        
        # より大きな試行回数でもmax_backoffを超えない
        backoff = strategy.get_backoff_with_jitter(20)
        assert backoff == 10.0
    
    def test_jitter_application(self):
        """ジッターが正しく適用されるか"""
        strategy = ExponentialBackoffStrategy(base=2.0, jitter_factor=0.2, max_backoff=300.0)
        # ジッターがあるため、正確な値ではなく範囲でテスト
        # attempt=2の場合、base値は4秒、ジッター±20%で3.2〜4.8秒
        backoffs = [strategy.get_backoff_with_jitter(2) for _ in range(100)]
        
        # すべてのバックオフが範囲内にあることを確認
        for backoff in backoffs:
            assert 3.2 <= backoff <= 4.8
        
        # 平均が期待値に近いことを確認
        avg = sum(backoffs) / len(backoffs)
        assert 3.5 <= avg <= 4.5
    
    def test_strategy_name(self):
        """戦略名が正しく取得できるか"""
        strategy = ExponentialBackoffStrategy()
        assert strategy.get_strategy_name() == "ExponentialBackoffStrategy"


class TestLinearBackoff:
    """線形バックオフ戦略のテスト"""
    
    def test_calculate_backoff(self):
        """線形バックオフの計算"""
        strategy = LinearBackoffStrategy(initial_delay=1.0, increment=2.0, jitter_factor=0.0)
        assert strategy.calculate_backoff(0) == 1.0
        assert strategy.calculate_backoff(1) == 3.0
        assert strategy.calculate_backoff(2) == 5.0
        assert strategy.calculate_backoff(3) == 7.0
        assert strategy.calculate_backoff(4) == 9.0
    
    def test_custom_parameters(self):
        """カスタムパラメータでの動作"""
        strategy = LinearBackoffStrategy(initial_delay=5.0, increment=10.0, jitter_factor=0.0)
        assert strategy.calculate_backoff(0) == 5.0
        assert strategy.calculate_backoff(1) == 15.0
        assert strategy.calculate_backoff(2) == 25.0
    
    def test_max_backoff(self):
        """最大バックオフ時間の制限"""
        strategy = LinearBackoffStrategy(
            initial_delay=1.0,
            increment=5.0,
            max_backoff=20.0,
            jitter_factor=0.0
        )
        # attempt=10 → 1 + 5*10 = 51秒だが、20秒に制限される
        backoff = strategy.get_backoff_with_jitter(10)
        assert backoff == 20.0
    
    def test_strategy_name(self):
        """戦略名の取得"""
        strategy = LinearBackoffStrategy()
        assert strategy.get_strategy_name() == "LinearBackoffStrategy"


class TestConstantBackoff:
    """固定間隔バックオフ戦略のテスト"""
    
    def test_calculate_backoff(self):
        """固定バックオフの計算"""
        strategy = ConstantBackoffStrategy(delay=5.0, jitter_factor=0.0)
        assert strategy.calculate_backoff(0) == 5.0
        assert strategy.calculate_backoff(1) == 5.0
        assert strategy.calculate_backoff(2) == 5.0
        assert strategy.calculate_backoff(10) == 5.0
        assert strategy.calculate_backoff(100) == 5.0
    
    def test_custom_delay(self):
        """カスタム遅延時間での動作"""
        strategy = ConstantBackoffStrategy(delay=10.0, jitter_factor=0.0)
        for i in range(20):
            assert strategy.calculate_backoff(i) == 10.0
    
    def test_jitter_with_constant(self):
        """固定間隔にもジッターが適用されるか"""
        strategy = ConstantBackoffStrategy(delay=10.0, jitter_factor=0.2)
        backoffs = [strategy.get_backoff_with_jitter(0) for _ in range(100)]
        
        # ジッター±20%で8.0〜12.0秒
        for backoff in backoffs:
            assert 8.0 <= backoff <= 12.0
        
        # 平均が期待値に近い
        avg = sum(backoffs) / len(backoffs)
        assert 9.0 <= avg <= 11.0
    
    def test_strategy_name(self):
        """戦略名の取得"""
        strategy = ConstantBackoffStrategy()
        assert strategy.get_strategy_name() == "ConstantBackoffStrategy"


class TestFibonacciBackoff:
    """フィボナッチバックオフ戦略のテスト"""
    
    def test_calculate_backoff(self):
        """フィボナッチバックオフの計算"""
        strategy = FibonacciBackoffStrategy(unit=1.0, jitter_factor=0.0)
        assert strategy.calculate_backoff(0) == 1
        assert strategy.calculate_backoff(1) == 1
        assert strategy.calculate_backoff(2) == 2
        assert strategy.calculate_backoff(3) == 3
        assert strategy.calculate_backoff(4) == 5
        assert strategy.calculate_backoff(5) == 8
        assert strategy.calculate_backoff(6) == 13
        assert strategy.calculate_backoff(7) == 21
    
    def test_custom_unit(self):
        """カスタム単位時間での動作"""
        strategy = FibonacciBackoffStrategy(unit=2.0, jitter_factor=0.0)
        assert strategy.calculate_backoff(0) == 2.0
        assert strategy.calculate_backoff(1) == 2.0
        assert strategy.calculate_backoff(2) == 4.0
        assert strategy.calculate_backoff(3) == 6.0
        assert strategy.calculate_backoff(4) == 10.0
    
    def test_max_backoff(self):
        """最大バックオフ時間の制限"""
        strategy = FibonacciBackoffStrategy(
            unit=1.0,
            max_backoff=15.0,
            jitter_factor=0.0
        )
        # fib(7) = 21だが、15秒に制限される
        backoff = strategy.get_backoff_with_jitter(7)
        assert backoff == 15.0
    
    def test_fibonacci_caching(self):
        """フィボナッチ数のキャッシュが正しく動作するか"""
        strategy = FibonacciBackoffStrategy(unit=1.0, jitter_factor=0.0)
        
        # 複数回呼び出しても同じ結果
        for _ in range(5):
            assert strategy.calculate_backoff(10) == 89
    
    def test_strategy_name(self):
        """戦略名の取得"""
        strategy = FibonacciBackoffStrategy()
        assert strategy.get_strategy_name() == "FibonacciBackoffStrategy"


class TestRetryStrategyBase:
    """リトライ戦略基底クラスの共通テスト"""
    
    def test_should_retry(self):
        """リトライ判定のテスト"""
        strategy = ExponentialBackoffStrategy()
        
        assert strategy.should_retry(0, 3) == True
        assert strategy.should_retry(1, 3) == True
        assert strategy.should_retry(2, 3) == True
        assert strategy.should_retry(3, 3) == False
        assert strategy.should_retry(4, 3) == False
    
    def test_jitter_disabled(self):
        """ジッター無効化のテスト"""
        strategy = ExponentialBackoffStrategy(base=2.0, jitter_factor=0.0)
        
        # ジッター0の場合、複数回呼び出しても同じ値
        backoffs = [strategy.get_backoff_with_jitter(3) for _ in range(10)]
        assert all(b == 8.0 for b in backoffs)
    
    def test_jitter_range(self):
        """ジッター範囲のテスト"""
        strategy = ExponentialBackoffStrategy(base=2.0, jitter_factor=0.3)
        
        # attempt=3の場合、base値は8秒、ジッター±30%で5.6〜10.4秒
        backoffs = [strategy.get_backoff_with_jitter(3) for _ in range(1000)]
        
        # すべてが範囲内
        for backoff in backoffs:
            assert 5.6 <= backoff <= 10.4
        
        # ジッターがランダムであることを確認（バリエーションがある）
        unique_values = set(backoffs)
        assert len(unique_values) > 100  # 十分なバリエーション
    
    def test_negative_jitter_prevention(self):
        """ジッターによる負の値の防止"""
        strategy = ExponentialBackoffStrategy(base=2.0, jitter_factor=2.0)
        
        # 非常に大きなジッター係数でも負にならない
        backoffs = [strategy.get_backoff_with_jitter(0) for _ in range(100)]
        assert all(b >= 0.0 for b in backoffs)
    
    def test_max_backoff_with_various_strategies(self):
        """すべての戦略でmax_backoffが機能するか"""
        strategies = [
            ExponentialBackoffStrategy(base=2.0, max_backoff=50.0, jitter_factor=0.0),
            LinearBackoffStrategy(initial_delay=10.0, increment=20.0, max_backoff=50.0, jitter_factor=0.0),
            ConstantBackoffStrategy(delay=100.0, max_backoff=50.0, jitter_factor=0.0),
            FibonacciBackoffStrategy(unit=10.0, max_backoff=50.0, jitter_factor=0.0)
        ]
        
        for strategy in strategies:
            # 大きな試行回数でもmax_backoffを超えない
            backoff = strategy.get_backoff_with_jitter(20)
            assert backoff <= 50.0, f"{strategy.get_strategy_name()} exceeded max_backoff"


class TestResilientStreamIntegration:
    """ResilientEventStreamとの統合テスト"""
    
    def test_custom_strategy_integration(self):
        """カスタム戦略がResilientEventStreamで使えるか"""
        from utils.resilient_event_stream import ResilientEventStream
        
        # 線形バックオフ戦略を使用
        strategy = LinearBackoffStrategy(
            initial_delay=1.0,
            increment=1.0,
            jitter_factor=0.0
        )
        stream = ResilientEventStream(
            retry_strategy=strategy,
            max_retries=2,
            enable_metrics=False
        )
        
        # 戦略が正しく設定されているか
        assert isinstance(stream.retry_strategy, LinearBackoffStrategy)
        assert stream.retry_strategy.get_strategy_name() == "LinearBackoffStrategy"
    
    def test_default_strategy(self):
        """デフォルト戦略がExponentialBackoffか"""
        from utils.resilient_event_stream import ResilientEventStream
        
        stream = ResilientEventStream(enable_metrics=False)
        
        assert isinstance(stream.retry_strategy, ExponentialBackoffStrategy)
        assert stream.retry_strategy.base == 2.0
        assert stream.retry_strategy.max_backoff == 300.0


if __name__ == "__main__":
    # pytest がない場合の簡易実行
    print("🧪 Running Retry Strategy Tests")
    print("=" * 60)
    
    test_classes = [
        TestExponentialBackoff,
        TestLinearBackoff,
        TestConstantBackoff,
        TestFibonacciBackoff,
        TestRetryStrategyBase,
        TestResilientStreamIntegration
    ]
    
    passed = 0
    failed = 0
    
    for test_class in test_classes:
        print(f"\n📋 {test_class.__name__}")
        print("-" * 60)
        
        test_instance = test_class()
        test_methods = [m for m in dir(test_instance) if m.startswith('test_')]
        
        for method_name in test_methods:
            try:
                method = getattr(test_instance, method_name)
                method()
                print(f"  ✅ {method_name}")
                passed += 1
            except AssertionError as e:
                print(f"  ❌ {method_name}: {e}")
                failed += 1
            except Exception as e:
                print(f"  ❌ {method_name}: Unexpected error: {e}")
                failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("✅ All tests passed!")
    else:
        print(f"❌ {failed} test(s) failed")

