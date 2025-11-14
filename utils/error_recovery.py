#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Error Recovery Module - エラーリカバリーモジュール
==================================================
自動リトライメカニズム、エラー分類、デッドレターキューの実装

機能:
1. 指数バックオフによる自動リトライ
2. エラー分類とリカバリー戦略
3. デッドレターキューの管理
"""

import sys
import time
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable, List
from enum import Enum

# utils/ からの import
sys.path.append(str(Path(__file__).parent))
from resonant_event_stream import get_stream


class ErrorCategory(Enum):
    """エラー分類"""
    NETWORK = "network"           # ネットワークエラー（リトライ可能）
    API_RATE_LIMIT = "rate_limit" # APIレート制限（リトライ可能、長時間待機）
    API_ERROR = "api_error"       # APIエラー（リトライ可能）
    AUTH_ERROR = "auth_error"     # 認証エラー（リトライ不可）
    VALIDATION_ERROR = "validation" # 検証エラー（リトライ不可）
    UNKNOWN = "unknown"           # 不明なエラー


class RetryStrategy:
    """リトライ戦略"""
    
    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
    
    def get_delay(self, attempt: int) -> float:
        """
        リトライ待機時間を計算（指数バックオフ）
        
        Args:
            attempt: リトライ試行回数（0から開始）
        
        Returns:
            待機時間（秒）
        """
        delay = self.initial_delay * (self.exponential_base ** attempt)
        delay = min(delay, self.max_delay)
        
        if self.jitter:
            # ジッターを追加（0.8倍〜1.2倍の範囲）
            import random
            jitter_factor = 0.8 + (random.random() * 0.4)
            delay = delay * jitter_factor
        
        return delay


class ErrorClassifier:
    """エラー分類器"""
    
    @staticmethod
    def classify_error(error: Exception) -> ErrorCategory:
        """
        エラーを分類
        
        Args:
            error: 例外オブジェクト
        
        Returns:
            エラー分類
        """
        error_str = str(error).lower()
        error_type = type(error).__name__
        
        # ネットワークエラー
        if any(keyword in error_str for keyword in ["connection", "timeout", "network", "unreachable"]):
            return ErrorCategory.NETWORK
        
        # レート制限
        if any(keyword in error_str for keyword in ["rate limit", "429", "too many requests", "quota"]):
            return ErrorCategory.API_RATE_LIMIT
        
        # 認証エラー
        if any(keyword in error_str for keyword in ["401", "403", "unauthorized", "forbidden", "authentication"]):
            return ErrorCategory.AUTH_ERROR
        
        # APIエラー
        if any(keyword in error_str for keyword in ["api", "500", "502", "503", "504", "service"]):
            return ErrorCategory.API_ERROR
        
        # 検証エラー
        if any(keyword in error_str for keyword in ["validation", "invalid", "400", "bad request"]):
            return ErrorCategory.VALIDATION_ERROR
        
        return ErrorCategory.UNKNOWN
    
    @staticmethod
    def is_retryable(error: Exception) -> bool:
        """
        エラーがリトライ可能かどうかを判定
        
        Args:
            error: 例外オブジェクト
        
        Returns:
            リトライ可能かどうか
        """
        category = ErrorClassifier.classify_error(error)
        return category in [
            ErrorCategory.NETWORK,
            ErrorCategory.API_RATE_LIMIT,
            ErrorCategory.API_ERROR
        ]
    
    @staticmethod
    def get_recovery_strategy(category: ErrorCategory) -> RetryStrategy:
        """
        エラー分類に応じたリカバリー戦略を取得
        
        Args:
            category: エラー分類
        
        Returns:
            リトライ戦略
        """
        if category == ErrorCategory.API_RATE_LIMIT:
            # レート制限の場合は長めの待機
            return RetryStrategy(
                max_retries=5,
                initial_delay=5.0,
                max_delay=300.0,  # 最大5分
                exponential_base=2.0
            )
        elif category == ErrorCategory.NETWORK:
            # ネットワークエラーは中程度の待機
            return RetryStrategy(
                max_retries=3,
                initial_delay=1.0,
                max_delay=60.0,
                exponential_base=2.0
            )
        elif category == ErrorCategory.API_ERROR:
            # APIエラーは短めの待機
            return RetryStrategy(
                max_retries=3,
                initial_delay=0.5,
                max_delay=30.0,
                exponential_base=2.0
            )
        else:
            # その他はデフォルト戦略
            return RetryStrategy(max_retries=0)


class DeadLetterQueue:
    """デッドレターキュー（リトライ不可能なエラーを保存）"""
    
    def __init__(self, dlq_path: Path = None):
        self.dlq_path = dlq_path or Path(__file__).parent.parent / "logs" / "dead_letter_queue.jsonl"
        self.dlq_path.parent.mkdir(parents=True, exist_ok=True)
    
    def add(
        self,
        event_id: str,
        error: Exception,
        error_category: ErrorCategory,
        context: Dict[str, Any],
        retry_count: int = 0
    ):
        """
        デッドレターキューに追加
        
        Args:
            event_id: イベントID
            error: 例外オブジェクト
            error_category: エラー分類
            context: コンテキスト情報
            retry_count: リトライ回数
        """
        entry = {
            "event_id": event_id,
            "timestamp": datetime.now().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "error_category": error_category.value,
            "retry_count": retry_count,
            "context": context
        }
        
        with open(self.dlq_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        
        print(f"⚠️ デッドレターキューに追加: {event_id} ({error_category.value})")
    
    def get_failed_events(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        失敗したイベントを取得
        
        Args:
            since: この日時以降のイベントのみ
        
        Returns:
            失敗したイベントのリスト
        """
        events = []
        if not self.dlq_path.exists():
            return events
        
        with open(self.dlq_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    event = json.loads(line)
                    if since:
                        event_time = datetime.fromisoformat(event["timestamp"])
                        if event_time < since:
                            continue
                    events.append(event)
                except json.JSONDecodeError:
                    continue
        
        return events


def with_retry(
    func: Callable,
    strategy: Optional[RetryStrategy] = None,
    error_context: Optional[Dict[str, Any]] = None,
    on_retry: Optional[Callable[[int, Exception], None]] = None,
    on_failure: Optional[Callable[[Exception], None]] = None
) -> Any:
    """
    自動リトライデコレータ関数
    
    Args:
        func: 実行する関数
        strategy: リトライ戦略（Noneの場合はデフォルト）
        error_context: エラーコンテキスト情報
        on_retry: リトライ時のコールバック（attempt, error）
        on_failure: 最終失敗時のコールバック（error）
    
    Returns:
        関数の戻り値
    
    Raises:
        最終的な例外（リトライ後に失敗した場合）
    """
    if strategy is None:
        strategy = RetryStrategy()
    
    error_context = error_context or {}
    last_error = None
    
    for attempt in range(strategy.max_retries + 1):
        try:
            return func()
        except Exception as e:
            last_error = e
            
            # リトライ不可能なエラーは即座に例外を投げる
            if not ErrorClassifier.is_retryable(e):
                if on_failure:
                    on_failure(e)
                raise e
            
            # 最大リトライ回数に達した場合は例外を投げる
            if attempt >= strategy.max_retries:
                if on_failure:
                    on_failure(e)
                raise e
            
            # リトライ待機
            delay = strategy.get_delay(attempt)
            if on_retry:
                on_retry(attempt + 1, e)
            
            time.sleep(delay)
    
    # ここに到達することはないが、念のため
    if on_failure and last_error:
        on_failure(last_error)
    raise last_error


# ============================================
# 使用例
# ============================================

if __name__ == "__main__":
    # テスト用
    def test_function():
        import random
        if random.random() < 0.7:
            raise ConnectionError("Network error")
        return "Success"
    
    try:
        result = with_retry(
            test_function,
            strategy=RetryStrategy(max_retries=3, initial_delay=0.1),
            on_retry=lambda attempt, error: print(f"リトライ {attempt}: {error}"),
            on_failure=lambda error: print(f"最終失敗: {error}")
        )
        print(f"結果: {result}")
    except Exception as e:
        print(f"エラー: {e}")

