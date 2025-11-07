#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Resilient Event Stream - P0改善: エラーリカバリー強化版
=====================================================
Event Schemaを拡張し、エラーハンドリングとリトライを強化
"""

import json
import uuid
import traceback
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List, Literal, Callable
from enum import Enum
import time

# リトライ戦略（P2-1）
from utils.retry_strategy import RetryStrategy, ExponentialBackoffStrategy

# メトリクス収集（P1-4）
try:
    from utils.metrics_collector import get_metrics_collector
    METRICS_ENABLED = True
except ImportError:
    METRICS_ENABLED = False

# イベントステータス
class EventStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"
    DEAD_LETTER = "dead_letter"  # リトライ上限到達

# エラー分類
class ErrorCategory(str, Enum):
    TRANSIENT = "transient"  # 一時的（リトライ可）
    PERMANENT = "permanent"  # 恒久的（リトライ不可）
    UNKNOWN = "unknown"

class ResilientEventStream:
    """
    拡張Event Schema + エラーリカバリー機能
    
    新しいフィールド:
    - status: イベントの実行ステータス
    - error_info: エラー詳細（category, message, stacktrace, context）
    - retry_info: リトライ情報（count, max_retries, next_retry_at）
    - recovery_actions: 実行したリカバリーアクション履歴
    """
    
    def __init__(self, 
                 stream_path: Path = None,
                 dead_letter_path: Path = None,
                 max_retries: int = 3,
                 retry_backoff_base: float = 2.0,
                 enable_metrics: bool = True,
                 retry_strategy: Optional[RetryStrategy] = None):
        """
        Args:
            stream_path: イベントストリームファイルパス
            dead_letter_path: デッドレターキューファイルパス
            max_retries: デフォルトの最大リトライ回数
            retry_backoff_base: エクスポネンシャルバックオフの基数（後方互換性のため残す）
            enable_metrics: メトリクス収集を有効化
            retry_strategy: リトライ戦略（Noneの場合はExponentialBackoff）
        """
        base_dir = Path(__file__).parent.parent / "logs"
        self.stream_path = stream_path or base_dir / "event_stream.jsonl"
        self.dead_letter_path = dead_letter_path or base_dir / "dead_letter_queue.jsonl"
        self.max_retries = max_retries
        self.retry_backoff_base = retry_backoff_base
        
        # リトライ戦略の初期化（P2-1, P2-3）
        if retry_strategy is None:
            # デフォルトはExponentialBackoff（既存動作を維持）
            self.retry_strategy = ExponentialBackoffStrategy(
                base=retry_backoff_base,
                max_backoff=300.0  # 5分上限（P2-3）
            )
        else:
            self.retry_strategy = retry_strategy
        
        self.stream_path.parent.mkdir(parents=True, exist_ok=True)
        self.dead_letter_path.parent.mkdir(parents=True, exist_ok=True)
        
        # メトリクス収集（P1-4）
        self.metrics_enabled = enable_metrics and METRICS_ENABLED
        if self.metrics_enabled:
            self.metrics = get_metrics_collector()
    
    def emit(self,
             event_type: str,
             source: str,
             data: Dict[str, Any],
             parent_event_id: Optional[str] = None,
             related_hypothesis_id: Optional[str] = None,
             tags: Optional[List[str]] = None,
             importance: int = 3,
             status: EventStatus = EventStatus.SUCCESS,
             error_info: Optional[Dict[str, Any]] = None,
             retry_info: Optional[Dict[str, Any]] = None,
             recovery_actions: Optional[List[Dict[str, Any]]] = None,
             latency_ms: Optional[int] = None,
             exit_code: Optional[int] = None
    ) -> str:
        """
        拡張されたイベント記録
        
        新規追加パラメータ:
            status: イベントステータス
            error_info: エラー詳細情報
            retry_info: リトライ情報
            recovery_actions: リカバリーアクション履歴
        """
        event_id = f"EVT-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
        
        event = {
            "event_id": event_id,
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "source": source,
            "data": data,
            "parent_event_id": parent_event_id,
            "related_hypothesis_id": related_hypothesis_id,
            "tags": tags or [],
            "importance": importance,
            "status": status.value,
            "error_info": error_info or {},
            "retry_info": retry_info or {},
            "recovery_actions": recovery_actions or [],
            "latency_ms": latency_ms,
            "exit_code": exit_code
        }
        
        # ステータスに応じてログ先を変更
        target_path = self.dead_letter_path if status == EventStatus.DEAD_LETTER else self.stream_path
        
        with open(target_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
        
        # メトリクス記録（P1-4）
        if self.metrics_enabled:
            self.metrics.record_event(
                status=status.value,
                error_category=error_info.get("category") if error_info else None,
                error_type=error_info.get("type") if error_info else None,
                retry_count=retry_info.get("count", 0) if retry_info else 0,
                latency_ms=latency_ms
            )
        
        status_emoji = {
            EventStatus.SUCCESS: "✅",
            EventStatus.PENDING: "⏳",
            EventStatus.FAILED: "❌",
            EventStatus.RETRYING: "🔄",
            EventStatus.DEAD_LETTER: "💀"
        }
        emoji = status_emoji.get(status, "📡")
        print(f"[{emoji} Event Emitted] {event_id}: {event_type} ({status.value})")
        
        return event_id
    
    def emit_with_retry(self,
                       event_type: str,
                       source: str,
                       action: Callable[[], Dict[str, Any]],
                       parent_event_id: Optional[str] = None,
                       related_hypothesis_id: Optional[str] = None,
                       tags: Optional[List[str]] = None,
                       importance: int = 3,
                       max_retries: Optional[int] = None,
                       timeout_seconds: Optional[float] = None
    ) -> str:
        """
        リトライ機能付きでアクションを実行してイベントを記録
        
        Args:
            action: 実行する関数（成功時は結果をDictで返す）
            max_retries: 最大リトライ回数（Noneの場合はデフォルト値）
            timeout_seconds: タイムアウト時間
            
        Returns:
            最終的に記録されたイベントID
        """
        max_retries = max_retries if max_retries is not None else self.max_retries
        retry_count = 0
        last_error = None
        recovery_actions = []
        
        while retry_count <= max_retries:
            try:
                start_time = time.time()
                
                # アクション実行
                result_data = action()
                
                latency_ms = int((time.time() - start_time) * 1000)
                
                # 成功イベントを記録
                return self.emit(
                    event_type=event_type,
                    source=source,
                    data=result_data,
                    parent_event_id=parent_event_id,
                    related_hypothesis_id=related_hypothesis_id,
                    tags=tags,
                    importance=importance,
                    status=EventStatus.SUCCESS,
                    latency_ms=latency_ms,
                    exit_code=0,
                    recovery_actions=recovery_actions if recovery_actions else None
                )
                
            except Exception as e:
                latency_ms = int((time.time() - start_time) * 1000)
                last_error = e
                error_category = self._classify_error(e)
                
                # エラー情報を構造化
                error_info = {
                    "category": error_category.value,
                    "message": str(e),
                    "type": type(e).__name__,
                    "stacktrace": traceback.format_exc(),
                    "context": {
                        "retry_count": retry_count,
                        "max_retries": max_retries
                    }
                }
                
                # 恒久的エラーの場合は即座に失敗
                if error_category == ErrorCategory.PERMANENT:
                    return self.emit(
                        event_type=event_type,
                        source=source,
                        data={"attempted_action": action.__name__},
                        parent_event_id=parent_event_id,
                        related_hypothesis_id=related_hypothesis_id,
                        tags=(tags or []) + ["error", "permanent_failure"],
                        importance=importance,
                        status=EventStatus.FAILED,
                        error_info=error_info,
                        latency_ms=latency_ms,
                        exit_code=1
                    )
                
                # リトライ可能な場合
                if retry_count < max_retries:
                    # バックオフ時間を計算（戦略ベース、ジッター適用済み）
                    backoff_seconds = self.retry_strategy.get_backoff_with_jitter(retry_count)
                    next_retry_at = datetime.now() + timedelta(seconds=backoff_seconds)
                    
                    retry_info = {
                        "count": retry_count + 1,
                        "max_retries": max_retries,
                        "next_retry_at": next_retry_at.isoformat(),
                        "backoff_seconds": backoff_seconds
                    }
                    
                    # リトライ中イベントを記録
                    retry_event_id = self.emit(
                        event_type=event_type,
                        source=source,
                        data={"attempted_action": action.__name__},
                        parent_event_id=parent_event_id,
                        related_hypothesis_id=related_hypothesis_id,
                        tags=(tags or []) + ["error", "retrying"],
                        importance=importance,
                        status=EventStatus.RETRYING,
                        error_info=error_info,
                        retry_info=retry_info,
                        latency_ms=latency_ms,
                        exit_code=1
                    )
                    
                    # リカバリーアクションを記録
                    recovery_actions.append({
                        "timestamp": datetime.now().isoformat(),
                        "action": self.retry_strategy.get_strategy_name(),
                        "backoff_seconds": backoff_seconds,
                        "event_id": retry_event_id
                    })
                    
                    print(f"[🔄 Retry] Attempt {retry_count + 1}/{max_retries}, waiting {backoff_seconds}s...")
                    time.sleep(backoff_seconds)
                    retry_count += 1
                else:
                    # リトライ上限到達 → デッドレターキュー
                    return self.emit(
                        event_type=event_type,
                        source=source,
                        data={"attempted_action": action.__name__},
                        parent_event_id=parent_event_id,
                        related_hypothesis_id=related_hypothesis_id,
                        tags=(tags or []) + ["error", "max_retries_exceeded"],
                        importance=5,  # 最高重要度
                        status=EventStatus.DEAD_LETTER,
                        error_info=error_info,
                        retry_info={
                            "count": retry_count,
                            "max_retries": max_retries,
                            "exhausted": True
                        },
                        recovery_actions=recovery_actions,
                        latency_ms=latency_ms,
                        exit_code=1
                    )
        
        # 理論的にここには到達しないが、念のため
        raise RuntimeError(f"Unexpected state in emit_with_retry: {last_error}")
    
    def _classify_error(self, error: Exception) -> ErrorCategory:
        """
        エラーを分類してリトライ可否を判定
        
        一時的エラー（リトライ推奨）:
        - TimeoutError, asyncio.TimeoutError
        - ConnectionError系
        - OSError (BrokenPipeError含む)
        - HTTPError (500系サーバーエラー)
        
        恒久的エラー（リトライ不要）:
        - ValueError (入力値の問題)
        - FileNotFoundError (存在しないリソース)
        - KeyError (データ構造の問題)
        - HTTPError (400系クライアントエラー)
        """
        import asyncio
        
        # HTTPErrorの特殊処理（500系はtransient、400系はpermanent）
        try:
            import requests
            if isinstance(error, requests.exceptions.HTTPError):
                # HTTPステータスコードを取得
                if hasattr(error, 'response') and error.response is not None:
                    status_code = error.response.status_code
                    if 500 <= status_code < 600:
                        return ErrorCategory.TRANSIENT  # サーバーエラー
                    elif 400 <= status_code < 500:
                        return ErrorCategory.PERMANENT  # クライアントエラー
        except ImportError:
            pass
        
        transient_errors = (
            TimeoutError,
            asyncio.TimeoutError,
            ConnectionError,
            ConnectionResetError,
            ConnectionAbortedError,
            ConnectionRefusedError,
            OSError,  # BrokenPipeError, BlockingIOError等を含む
            BrokenPipeError,
        )
        
        permanent_errors = (
            ValueError,
            KeyError,
            FileNotFoundError,
            TypeError,
            AttributeError,
        )
        
        if isinstance(error, transient_errors):
            return ErrorCategory.TRANSIENT
        elif isinstance(error, permanent_errors):
            return ErrorCategory.PERMANENT
        else:
            return ErrorCategory.UNKNOWN
    
    def get_failed_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """失敗したイベントを取得"""
        return self._query_by_status(EventStatus.FAILED, limit)
    
    def get_dead_letter_queue(self, limit: int = 100) -> List[Dict[str, Any]]:
        """デッドレターキューのイベントを取得"""
        events = []
        if not self.dead_letter_path.exists():
            return events
        
        with open(self.dead_letter_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        
        return events[-limit:][::-1]
    
    def get_retry_candidates(self) -> List[Dict[str, Any]]:
        """手動リトライ候補（デッドレターキュー内で一時的エラー）を取得"""
        dlq_events = self.get_dead_letter_queue()
        candidates = []
        
        for event in dlq_events:
            error_info = event.get("error_info", {})
            if error_info.get("category") == ErrorCategory.TRANSIENT.value:
                candidates.append(event)
        
        return candidates
    
    def _query_by_status(self, status: EventStatus, limit: int = 100) -> List[Dict[str, Any]]:
        """ステータスでイベントを検索"""
        events = []
        if not self.stream_path.exists():
            return events
        
        with open(self.stream_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    event = json.loads(line)
                    if event.get("status") == status.value:
                        events.append(event)
                except json.JSONDecodeError:
                    continue
        
        return events[-limit:][::-1]


# グローバルインスタンス
_resilient_stream = None

def get_resilient_stream() -> ResilientEventStream:
    """シングルトンの Resilient Event Stream を取得"""
    global _resilient_stream
    if _resilient_stream is None:
        _resilient_stream = ResilientEventStream()
    return _resilient_stream


if __name__ == "__main__":
    # デモ実行
    stream = ResilientEventStream(max_retries=3)
    
    print("=== P0改善デモ: Event Schema拡張 + エラーリカバリー ===\n")
    
    # ケース1: 成功するアクション
    def successful_action():
        return {"result": "success", "data": {"value": 42}}
    
    print("[ケース1] 成功するアクション")
    event_id_1 = stream.emit_with_retry(
        event_type="action",
        source="demo",
        action=successful_action,
        tags=["demo", "success"]
    )
    print()
    
    # ケース2: 一時的エラー（リトライ後に成功）
    attempt_count = {"count": 0}
    def transient_error_action():
        attempt_count["count"] += 1
        if attempt_count["count"] < 3:
            raise ConnectionError("Network temporarily unavailable")
        return {"result": "recovered", "attempts": attempt_count["count"]}
    
    print("[ケース2] 一時的エラー → リトライで成功")
    event_id_2 = stream.emit_with_retry(
        event_type="action",
        source="demo",
        action=transient_error_action,
        tags=["demo", "transient_error"]
    )
    print()
    
    # ケース3: 恒久的エラー（即座に失敗）
    def permanent_error_action():
        raise ValueError("Invalid input parameters")
    
    print("[ケース3] 恒久的エラー → 即座に失敗")
    event_id_3 = stream.emit_with_retry(
        event_type="action",
        source="demo",
        action=permanent_error_action,
        tags=["demo", "permanent_error"]
    )
    print()
    
    # ケース4: リトライ上限到達 → デッドレターキュー
    def always_fails_action():
        raise TimeoutError("Service unavailable")
    
    print("[ケース4] リトライ上限到達 → デッドレターキュー")
    event_id_4 = stream.emit_with_retry(
        event_type="action",
        source="demo",
        action=always_fails_action,
        tags=["demo", "dead_letter"],
        max_retries=2
    )
    print()
    
    # 統計表示
    print("=== エラー統計 ===")
    print(f"失敗イベント: {len(stream.get_failed_events())}件")
    print(f"デッドレターキュー: {len(stream.get_dead_letter_queue())}件")
    print(f"手動リトライ候補: {len(stream.get_retry_candidates())}件")
    
    print("\n=== デッドレターキュー詳細 ===")
    for event in stream.get_dead_letter_queue():
        error_info = event.get("error_info", {})
        print(f"- {event['event_id']}: {error_info.get('message')}")
        print(f"  Category: {error_info.get('category')}")
        print(f"  Retries: {event['retry_info'].get('count')}")
        print()
