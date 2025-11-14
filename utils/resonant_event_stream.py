#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Resonant Event Stream - 全イベントの統一記録層
================================================
すべての行動・意図・結果を1つの時系列ストリームに記録し、
システム全体の因果関係を追跡可能にする。

これまで分散していた：
- intent_log.jsonl
- webhook_log.jsonl
- hypothesis_trace_log.json
- observer_daemon.log

を統合し、「点」を「線」に変える。

Event Type Taxonomy（イベント種別分類）:
- intent: 人間またはAIの意図表明
- action: システムの行動（Git pull、Webhook受信など）
- result: 行動の結果
- observation: 観測・監視イベント
- hypothesis: 仮説の記録・更新
- error: エラーイベント（専用）
- retry: リトライイベント
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

class ResonantEventStream:
    """
    全システムイベントの統一記録ストリーム
    
    イベント種別:
    - intent: 人間またはAIの意図表明
    - action: システムの行動（Git pull、Webhook受信など）
    - result: 行動の結果
    - observation: 観測・監視イベント
    - hypothesis: 仮説の記録・更新
    """
    
    def __init__(self, stream_path: Path = None):
        self.stream_path = stream_path or Path(__file__).parent.parent / "logs" / "event_stream.jsonl"
        self.stream_path.parent.mkdir(parents=True, exist_ok=True)
    
    def emit(self, 
             event_type: str,
             source: str,
             data: Dict[str, Any],
             parent_event_id: Optional[str] = None,
             related_hypothesis_id: Optional[str] = None,
             tags: Optional[List[str]] = None,
             latency_ms: Optional[int] = None,
             exit_code: Optional[int] = None,
             importance: int = 3,
             status: Optional[str] = None,
             error_info: Optional[Dict[str, Any]] = None,
             retry_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        統一イベントを記録し、イベントIDを返す
        
        Args:
            event_type: イベント種別 (intent/action/result/observation/hypothesis)
            source: イベント発生源 (observer_daemon/github_webhook/user/backlog)
            data: イベント固有のデータ
            parent_event_id: 親イベントID（因果関係）
            related_hypothesis_id: 関連する仮説ID
            tags: タグリスト（検索用）
            latency_ms: 処理時間（ミリ秒）
            exit_code: コマンド実行結果（0=成功、非0=失敗）
            importance: 重要度（1=低 ~ 5=高、デフォルト=3）
            status: ステータス（pending/running/success/failed/retrying）
            error_info: エラー情報（error_type, error_message, error_category, stack_trace等）
            retry_info: リトライ情報（retry_count, max_retries, next_retry_at等）
        
        Returns:
            生成されたイベントID
        """
        event_id = f"EVT-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
        
        # ステータスの自動判定
        if status is None:
            if exit_code is not None:
                status = "success" if exit_code == 0 else "failed"
            elif error_info:
                status = "failed"
            elif retry_info:
                status = "retrying"
            else:
                status = "pending"
        
        event = {
            "event_id": event_id,
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "source": source,
            "data": data,
            "parent_event_id": parent_event_id,
            "related_hypothesis_id": related_hypothesis_id,
            "tags": tags or [],
            "latency_ms": latency_ms,
            "exit_code": exit_code,
            "importance": importance,
            "status": status,
            "error_info": error_info,
            "retry_info": retry_info
        }
        
        with open(self.stream_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
        
        print(f"[📡 Event Emitted] {event_id}: {event_type} from {source} [{status}]")
        return event_id
    
    def query(self, 
              event_type: Optional[str] = None,
              source: Optional[str] = None,
              related_hypothesis_id: Optional[str] = None,
              tags: Optional[List[str]] = None,
              since: Optional[datetime] = None,
              limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        イベントストリームを検索
        
        Args:
            event_type: イベント種別でフィルタ
            source: 発生源でフィルタ
            related_hypothesis_id: 仮説IDでフィルタ
            tags: タグでフィルタ（OR条件）
            since: この日時以降のイベントのみ
            limit: 最大取得件数
        
        Returns:
            マッチしたイベントのリスト（新しい順）
        """
        events = []
        if not self.stream_path.exists():
            return events
            
        with open(self.stream_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                
                # フィルタリング
                if event_type and event["event_type"] != event_type:
                    continue
                if source and event["source"] != source:
                    continue
                if related_hypothesis_id and event.get("related_hypothesis_id") != related_hypothesis_id:
                    continue
                if tags:
                    event_tags = set(event.get("tags", []))
                    if not any(tag in event_tags for tag in tags):
                        continue
                if since:
                    try:
                        event_time = datetime.fromisoformat(event["timestamp"])
                        if event_time < since:
                            continue
                    except ValueError:
                        continue
                
                events.append(event)
                
                if len(events) >= limit:
                    break
        
        return events[::-1]  # 新しい順
    
    def trace_causality(self, event_id: str) -> List[Dict[str, Any]]:
        """
        あるイベントの因果関係を逆順にたどる
        
        例:
        - EVT-001: ユーザーが意図を記録
        - EVT-002: observer_daemonがGit変更を検知（parent: EVT-001）
        - EVT-003: Git pullを実行（parent: EVT-002）
        - EVT-004: 仮説を検証（parent: EVT-003）
        
        trace_causality("EVT-004") → [EVT-001, EVT-002, EVT-003, EVT-004]
        
        Args:
            event_id: トレース開始イベントID
        
        Returns:
            因果関係チェーン（時系列順）
        """
        chain = []
        current_id = event_id
        
        if not self.stream_path.exists():
            return chain
        
        with open(self.stream_path, "r", encoding="utf-8") as f:
            events = []
            for line in f:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        
        events_by_id = {e["event_id"]: e for e in events}
        
        # 親を辿っていく
        visited = set()
        while current_id and current_id not in visited:
            if current_id not in events_by_id:
                break
            event = events_by_id[current_id]
            chain.append(event)
            visited.add(current_id)
            current_id = event.get("parent_event_id")
        
        return chain[::-1]  # 時系列順に並び替え
    
    def get_timeline(self, hypothesis_id: str) -> List[Dict[str, Any]]:
        """
        特定の仮説に関連する全イベントを時系列で取得
        
        Args:
            hypothesis_id: 仮説ID
        
        Returns:
            関連イベントのタイムライン
        """
        return self.query(related_hypothesis_id=hypothesis_id, limit=1000)


# グローバルインスタンス（各デーモンから使う）
_global_stream = None

def get_stream() -> ResonantEventStream:
    """シングルトンのグローバルストリームを取得"""
    global _global_stream
    if _global_stream is None:
        _global_stream = ResonantEventStream()
    return _global_stream


if __name__ == "__main__":
    # テスト実行
    stream = ResonantEventStream()
    
    # テストイベント1: 意図の記録
    intent_id = stream.emit(
        event_type="intent",
        source="user",
        data={
            "intent": "observer_daemonのテスト",
            "description": "外部更新の自動同期をテスト"
        },
        tags=["test", "observer_daemon"]
    )
    
    # テストイベント2: 行動（親イベントを指定）
    action_id = stream.emit(
        event_type="action",
        source="observer_daemon",
        data={
            "action": "git_pull",
            "target": "origin/main"
        },
        parent_event_id=intent_id,
        tags=["git", "sync"]
    )
    
    # テストイベント3: 結果
    result_id = stream.emit(
        event_type="result",
        source="observer_daemon",
        data={
            "status": "success",
            "files_changed": 3,
            "commit": "abc123"
        },
        parent_event_id=action_id
    )
    
    print("\n[因果関係トレース]")
    chain = stream.trace_causality(result_id)
    for i, event in enumerate(chain, 1):
        print(f"{i}. {event['event_type']} from {event['source']}: {event['data']}")
    
    print("\n[最近のイベント検索]")
    recent = stream.query(limit=10)
    for event in recent:
        print(f"- {event['timestamp']}: {event['event_type']} ({event['source']})")

