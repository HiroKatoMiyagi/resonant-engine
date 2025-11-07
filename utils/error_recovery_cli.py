#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Error Recovery CLI - エラーイベントの管理・再実行ツール
=====================================================
デッドレターキューやエラーイベントを確認・再実行するCLI
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.resilient_event_stream import ResilientEventStream, EventStatus, ErrorCategory
from utils.metrics_collector import get_metrics_collector

class ErrorRecoveryCLI:
    """エラーリカバリー用CLIツール"""
    
    def __init__(self):
        self.stream = ResilientEventStream()
        self.metrics = get_metrics_collector()
    
    def show_status(self):
        """エラー状況の概要を表示"""
        print("=" * 60)
        print("📊 Resonant Engine - Error Recovery Status")
        print("=" * 60)
        print()
        
        # 統計情報
        failed = self.stream.get_failed_events()
        dlq = self.stream.get_dead_letter_queue()
        retry_candidates = self.stream.get_retry_candidates()
        
        print(f"❌ Failed Events: {len(failed)}")
        print(f"💀 Dead Letter Queue: {len(dlq)}")
        print(f"🔄 Retry Candidates: {len(retry_candidates)}")
        print()
        
        if not dlq and not failed:
            print("✅ No errors detected - system is healthy!")
            return
        
        # エラーカテゴリ別集計
        error_by_category = {}
        for event in dlq + failed:
            error_info = event.get("error_info", {})
            category = error_info.get("category", "unknown")
            error_by_category[category] = error_by_category.get(category, 0) + 1
        
        print("Error Breakdown:")
        for category, count in error_by_category.items():
            emoji = "⚡" if category == "transient" else "🚫" if category == "permanent" else "❓"
            print(f"  {emoji} {category}: {count}")
        print()
    
    def list_dead_letter_queue(self, limit: int = 20):
        """デッドレターキューを一覧表示"""
        print("=" * 60)
        print("💀 Dead Letter Queue")
        print("=" * 60)
        print()
        
        dlq_events = self.stream.get_dead_letter_queue(limit=limit)
        
        if not dlq_events:
            print("✅ Dead letter queue is empty!")
            return
        
        for i, event in enumerate(dlq_events, 1):
            self._print_event_summary(i, event, show_details=False)
    
    def list_failed_events(self, limit: int = 20):
        """失敗イベントを一覧表示"""
        print("=" * 60)
        print("❌ Failed Events")
        print("=" * 60)
        print()
        
        failed = self.stream.get_failed_events(limit=limit)
        
        if not failed:
            print("✅ No failed events!")
            return
        
        for i, event in enumerate(failed, 1):
            self._print_event_summary(i, event, show_details=False)
    
    def list_retry_candidates(self):
        """リトライ候補を一覧表示"""
        print("=" * 60)
        print("🔄 Retry Candidates (Transient Errors)")
        print("=" * 60)
        print()
        
        candidates = self.stream.get_retry_candidates()
        
        if not candidates:
            print("✅ No retry candidates found!")
            return
        
        for i, event in enumerate(candidates, 1):
            self._print_event_summary(i, event, show_details=True)
    
    def show_event_detail(self, event_id: str):
        """特定イベントの詳細を表示"""
        print("=" * 60)
        print(f"🔍 Event Detail: {event_id}")
        print("=" * 60)
        print()
        
        # イベントを検索
        event = self._find_event(event_id)
        
        if not event:
            print(f"❌ Event not found: {event_id}")
            return
        
        # 詳細情報を表示
        print(f"Event ID: {event['event_id']}")
        print(f"Timestamp: {event['timestamp']}")
        print(f"Type: {event['event_type']}")
        print(f"Source: {event['source']}")
        print(f"Status: {event['status']}")
        print()
        
        # エラー情報
        if event.get("error_info"):
            print("Error Information:")
            error_info = event["error_info"]
            print(f"  Category: {error_info.get('category')}")
            print(f"  Type: {error_info.get('type')}")
            print(f"  Message: {error_info.get('message')}")
            print()
            
            if error_info.get("stacktrace"):
                print("Stack Trace:")
                print(error_info["stacktrace"])
                print()
        
        # リトライ情報
        if event.get("retry_info"):
            print("Retry Information:")
            retry_info = event["retry_info"]
            print(f"  Count: {retry_info.get('count')}/{retry_info.get('max_retries')}")
            if retry_info.get("next_retry_at"):
                print(f"  Next Retry: {retry_info['next_retry_at']}")
            print()
        
        # リカバリーアクション
        if event.get("recovery_actions"):
            print("Recovery Actions:")
            for action in event["recovery_actions"]:
                print(f"  - {action['timestamp']}: {action['action']}")
            print()
        
        # データ
        print("Event Data:")
        print(json.dumps(event.get("data", {}), indent=2, ensure_ascii=False))
        print()
    
    def export_errors_report(self, output_path: str = "error_report.json"):
        """エラーレポートをエクスポート"""
        report = {
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "failed_events": len(self.stream.get_failed_events()),
                "dead_letter_queue": len(self.stream.get_dead_letter_queue()),
                "retry_candidates": len(self.stream.get_retry_candidates())
            },
            "dead_letter_queue": self.stream.get_dead_letter_queue(),
            "failed_events": self.stream.get_failed_events(),
            "retry_candidates": self.stream.get_retry_candidates()
        }
        
        output = Path(output_path)
        with open(output, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Error report exported to: {output.absolute()}")
    
    def retry_event(self, event_id: str):
        """手動でイベントをリトライ"""
        print(f"🔄 Retrying event: {event_id}")
        print()
        
        # イベントを検索
        event = self._find_event(event_id)
        
        if not event:
            print(f"❌ Event not found: {event_id}")
            return
        
        # エラー情報を確認
        error_info = event.get("error_info", {})
        error_category = error_info.get("category")
        
        if error_category == "permanent":
            print(f"⚠️  Warning: This event has a permanent error.")
            print(f"   Error: {error_info.get('message')}")
            print(f"   Retrying may not resolve the issue.")
            print()
            response = input("Continue anyway? (y/N): ")
            if response.lower() != 'y':
                print("❌ Retry cancelled.")
                return
        
        # リトライ実行（シミュレーション）
        # 注意: 実際のリトライには、元のactionの再実行が必要
        # 現在はイベントログにリトライ記録を追加
        print("📝 Recording retry attempt...")
        
        retry_event_data = {
            "original_event_id": event_id,
            "retry_type": "manual",
            "retry_timestamp": datetime.now().isoformat(),
            "original_error": error_info.get('message')
        }
        
        new_event_id = self.stream.emit(
            event_type="manual_retry",
            source="error_recovery_cli",
            data=retry_event_data,
            parent_event_id=event_id,
            tags=["manual_retry", "recovery"],
            importance=4,
            status=EventStatus.PENDING
        )
        
        print(f"✅ Retry recorded: {new_event_id}")
        print()
        print("💡 Note: This is a manual retry record.")
        print("   To actually re-execute the action, you need to:")
        print("   1. Identify the original action from event data")
        print("   2. Re-execute it programmatically or manually")
        print()
    
    def show_metrics(self):
        """メトリクスサマリーを表示"""
        print("=" * 60)
        print("📊 Metrics Summary")
        print("=" * 60)
        print()
        
        summary = self.metrics.get_summary()
        
        # 基本統計
        print("📈 Event Statistics:")
        print(f"  Total Events: {summary['total_events']}")
        print(f"  Success: {summary['success_events']} ({summary['success_rate']}%)")
        print(f"  Failed: {summary['failed_events']} ({summary['error_rate']}%)")
        print(f"  Dead Letter: {summary['dead_letter_events']}")
        print()
        
        # エラーカテゴリ
        if summary.get('error_categories'):
            print("⚡ Error Categories:")
            for category, count in summary['error_categories'].items():
                print(f"  {category}: {count}")
            print()
        
        # エラータイプ
        if summary.get('error_types'):
            print("🚫 Error Types:")
            for error_type, count in summary['error_types'].items():
                print(f"  {error_type}: {count}")
            print()
        
        # レイテンシー
        if summary.get('latency_stats'):
            latency = summary['latency_stats']
            print("⏱️ Latency (ms):")
            print(f"  Min: {latency.get('min', 0):.0f}")
            print(f"  Avg: {latency.get('avg', 0):.0f}")
            print(f"  P50: {latency.get('p50', 0):.0f}")
            print(f"  P95: {latency.get('p95', 0):.0f}")
            print(f"  P99: {latency.get('p99', 0):.0f}")
            print(f"  Max: {latency.get('max', 0):.0f}")
            print()
        
        # リトライ
        if summary.get('retry_stats'):
            retry = summary['retry_stats']
            print("🔄 Retry Statistics:")
            print(f"  Total Retries: {retry.get('total_retries', 0)}")
            print(f"  Avg Retries: {retry.get('avg_retries', 0):.2f}")
            print(f"  Max Retries: {retry.get('max_retries', 0)}")
            print()
        
        print(f"⌛ Last Updated: {summary.get('last_updated', 'N/A')}")
        print()
    
    def export_prometheus(self, output_path: str = "metrics.prom"):
        """メトリクスをPrometheus形式でエクスポート"""
        prom_data = self.metrics.export_prometheus_format()
        
        output = Path(output_path)
        with open(output, "w", encoding="utf-8") as f:
            f.write(prom_data)
        
        print(f"✅ Prometheus metrics exported to: {output.absolute()}")
        print()
    
    def purge_old_events(self, days: int):
        """古いDLQイベントを削除"""
        print(f"🗑️  Purging events older than {days} days...")
        print()
        
        if not self.stream.dead_letter_path.exists():
            print("✅ Dead letter queue is empty.")
            return
        
        # 現在のタイムスタンプ
        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # DLQを読み込んでフィルター
        kept_events = []
        purged_count = 0
        
        with open(self.stream.dead_letter_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    event = json.loads(line)
                    event_time = datetime.fromisoformat(event["timestamp"])
                    
                    if event_time >= cutoff_date:
                        kept_events.append(event)
                    else:
                        purged_count += 1
                except (json.JSONDecodeError, ValueError, KeyError):
                    continue
        
        # ファイルを上書き
        with open(self.stream.dead_letter_path, "w", encoding="utf-8") as f:
            for event in kept_events:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
        
        print(f"✅ Purged {purged_count} events.")
        print(f"   Kept {len(kept_events)} events.")
        print()
    
    def _print_event_summary(self, index: int, event: Dict[str, Any], show_details: bool = False):
        """イベントのサマリーを表示"""
        error_info = event.get("error_info", {})
        retry_info = event.get("retry_info", {})
        
        category_emoji = {
            "transient": "⚡",
            "permanent": "🚫",
            "unknown": "❓"
        }
        emoji = category_emoji.get(error_info.get("category"), "❓")
        
        print(f"{index}. [{emoji}] {event['event_id']}")
        print(f"   Timestamp: {event['timestamp']}")
        print(f"   Source: {event['source']} | Type: {event['event_type']}")
        print(f"   Error: {error_info.get('message', 'N/A')}")
        
        if retry_info:
            print(f"   Retries: {retry_info.get('count', 0)}/{retry_info.get('max_retries', 0)}")
        
        if show_details and error_info.get("category") == "transient":
            print(f"   💡 Suggestion: This error may be transient. Consider manual retry.")
        
        print()
    
    def _find_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """イベントIDでイベントを検索"""
        # まずメインストリームを検索
        if self.stream.stream_path.exists():
            with open(self.stream.stream_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        event = json.loads(line)
                        if event["event_id"] == event_id:
                            return event
                    except json.JSONDecodeError:
                        continue
        
        # デッドレターキューも検索
        if self.stream.dead_letter_path.exists():
            with open(self.stream.dead_letter_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        event = json.loads(line)
                        if event["event_id"] == event_id:
                            return event
                    except json.JSONDecodeError:
                        continue
        
        return None


def main():
    """CLIエントリーポイント"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Error Recovery CLI - Manage failed events and dead letter queue"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # status コマンド
    subparsers.add_parser("status", help="Show error recovery status")
    
    # dlq コマンド
    dlq_parser = subparsers.add_parser("dlq", help="List dead letter queue")
    dlq_parser.add_argument("--limit", type=int, default=20, help="Maximum events to show")
    
    # failed コマンド
    failed_parser = subparsers.add_parser("failed", help="List failed events")
    failed_parser.add_argument("--limit", type=int, default=20, help="Maximum events to show")
    
    # retry-candidates コマンド
    subparsers.add_parser("retry-candidates", help="List retry candidates")
    
    # detail コマンド
    detail_parser = subparsers.add_parser("detail", help="Show event detail")
    detail_parser.add_argument("event_id", help="Event ID to inspect")
    
    # export コマンド
    export_parser = subparsers.add_parser("export", help="Export error report")
    export_parser.add_argument("--output", default="error_report.json", help="Output file path")
    
    # retry コマンド (P1-3: 新規追加)
    retry_parser = subparsers.add_parser("retry", help="Manually retry an event from DLQ")
    retry_parser.add_argument("event_id", help="Event ID to retry")
    
    # purge コマンド (P1-3: 新規追加)
    purge_parser = subparsers.add_parser("purge", help="Purge old DLQ events")
    purge_parser.add_argument("--older-than", type=int, default=30, help="Delete events older than N days (default: 30)")
    
    # metrics コマンド (P1-4: 新規追加)
    subparsers.add_parser("metrics", help="Show metrics summary")
    
    # prometheus コマンド (P1-4: 新規追加)
    prom_parser = subparsers.add_parser("prometheus", help="Export Prometheus metrics")
    prom_parser.add_argument("--output", default="metrics.prom", help="Output file path")
    
    args = parser.parse_args()
    
    cli = ErrorRecoveryCLI()
    
    if args.command == "status":
        cli.show_status()
    elif args.command == "dlq":
        cli.list_dead_letter_queue(limit=args.limit)
    elif args.command == "failed":
        cli.list_failed_events(limit=args.limit)
    elif args.command == "retry-candidates":
        cli.list_retry_candidates()
    elif args.command == "detail":
        cli.show_event_detail(args.event_id)
    elif args.command == "export":
        cli.export_errors_report(output_path=args.output)
    elif args.command == "retry":  # P1-3: 新規追加
        cli.retry_event(args.event_id)
    elif args.command == "purge":  # P1-3: 新規追加
        cli.purge_old_events(days=args.older_than)
    elif args.command == "metrics":  # P1-4: 新規追加
        cli.show_metrics()
    elif args.command == "prometheus":  # P1-4: 新規追加
        cli.export_prometheus(output_path=args.output)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
