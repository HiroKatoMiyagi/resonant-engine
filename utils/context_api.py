#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Resonant Context API - 開発文脈提供API
======================================
AI（Cursor）がプロジェクトの文脈を理解するためのAPIを提供。

機能:
1. 直近の変更と意図を取得
2. 特定機能の仕様変更履歴を取得
3. プロジェクトの現状をサマリー
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# utils/ からの import
sys.path.append(str(Path(__file__).parent))
from resonant_event_stream import get_stream


class ResonantContextAPI:
    """
    開発文脈を提供するAPIクラス
    
    AIがプロジェクトの状態を理解するための情報を提供します。
    """
    
    def __init__(self):
        self.stream = get_stream()
    
    def get_recent_changes(self, days: int = 7) -> Dict[str, Any]:
        """
        直近の変更と意図を返す
        
        Args:
            days: 分析対象の日数（デフォルト: 7日）
        
        Returns:
            直近の変更情報を含む辞書
        """
        since = datetime.now() - timedelta(days=days)
        events = self.stream.query(since=since, limit=1000)
        
        # イベントを分類
        intents = [e for e in events if e["event_type"] == "intent"]
        actions = [e for e in events if e["event_type"] == "action"]
        results = [e for e in events if e["event_type"] == "result"]
        
        # 意図を時系列で整理
        recent_intents = []
        for intent in sorted(intents, key=lambda x: x["timestamp"], reverse=True)[:10]:
            recent_intents.append({
                "timestamp": intent["timestamp"],
                "intent": intent["data"].get("intent", ""),
                "context": intent["data"].get("context", ""),
                "source": intent["source"]
            })
        
        # 主要なアクションを整理
        recent_actions = []
        for action in sorted(actions, key=lambda x: x["timestamp"], reverse=True)[:20]:
            recent_actions.append({
                "timestamp": action["timestamp"],
                "action": action["data"].get("action", ""),
                "source": action["source"],
                "data": action["data"]
            })
        
        # 結果を整理（成功/失敗）
        success_count = sum(1 for r in results if r["data"].get("status") == "success")
        error_count = sum(1 for r in results if r["data"].get("status") == "error")
        recent_errors = []
        for result in sorted(results, key=lambda x: x["timestamp"], reverse=True):
            if result["data"].get("status") == "error":
                recent_errors.append({
                    "timestamp": result["timestamp"],
                    "error": result["data"].get("error", ""),
                    "source": result["source"]
                })
                if len(recent_errors) >= 5:
                    break
        
        return {
            "period_days": days,
            "generated_at": datetime.now().isoformat(),
            "intents": recent_intents,
            "actions": recent_actions,
            "summary": {
                "total_events": len(events),
                "intents_count": len(intents),
                "actions_count": len(actions),
                "results_count": len(results),
                "success_count": success_count,
                "error_count": error_count
            },
            "recent_errors": recent_errors
        }
    
    def get_spec_history(self, feature_name: str) -> Dict[str, Any]:
        """
        特定機能の仕様変更履歴を取得
        
        Args:
            feature_name: 機能名（検索キーワード）
        
        Returns:
            仕様変更履歴を含む辞書
        """
        # Notion同期イベントから仕様書関連を検索
        events = self.stream.query(source="notion_sync", limit=500)
        
        spec_events = []
        for event in events:
            data = event.get("data", {})
            spec_name = data.get("spec_name", "")
            
            # 機能名を含むイベントを検索
            if feature_name.lower() in spec_name.lower() or \
               feature_name.lower() in str(data).lower():
                spec_events.append({
                    "timestamp": event["timestamp"],
                    "event_type": event["event_type"],
                    "spec_name": spec_name,
                    "page_id": data.get("page_id", ""),
                    "status": data.get("status", ""),
                    "memo": data.get("memo", "")
                })
        
        # 時系列でソート
        spec_events.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return {
            "feature_name": feature_name,
            "generated_at": datetime.now().isoformat(),
            "events": spec_events,
            "total_events": len(spec_events)
        }
    
    def summarize_project_state(self) -> Dict[str, Any]:
        """
        プロジェクトの現状をサマリー
        
        Returns:
            プロジェクトの現状を含む辞書
        """
        # 直近30日間のイベントを分析
        since_30d = datetime.now() - timedelta(days=30)
        events_30d = self.stream.query(since=since_30d, limit=1000)
        
        # 直近7日間のイベントを分析
        since_7d = datetime.now() - timedelta(days=7)
        events_7d = self.stream.query(since=since_7d, limit=1000)
        
        # ソース別の統計
        sources_30d = {}
        sources_7d = {}
        
        for event in events_30d:
            source = event["source"]
            sources_30d[source] = sources_30d.get(source, 0) + 1
        
        for event in events_7d:
            source = event["source"]
            sources_7d[source] = sources_7d.get(source, 0) + 1
        
        # イベント種別の統計
        event_types_30d = {}
        event_types_7d = {}
        
        for event in events_30d:
            event_type = event["event_type"]
            event_types_30d[event_type] = event_types_30d.get(event_type, 0) + 1
        
        for event in events_7d:
            event_type = event["event_type"]
            event_types_7d[event_type] = event_types_7d.get(event_type, 0) + 1
        
        # 最新の意図
        latest_intents = []
        for event in sorted(events_7d, key=lambda x: x["timestamp"], reverse=True):
            if event["event_type"] == "intent":
                latest_intents.append({
                    "timestamp": event["timestamp"],
                    "intent": event["data"].get("intent", ""),
                    "source": event["source"]
                })
                if len(latest_intents) >= 5:
                    break
        
        # エラー率の計算
        results_30d = [e for e in events_30d if e["event_type"] == "result"]
        errors_30d = [e for e in results_30d if e["data"].get("status") == "error"]
        error_rate_30d = len(errors_30d) / len(results_30d) * 100 if results_30d else 0
        
        results_7d = [e for e in events_7d if e["event_type"] == "result"]
        errors_7d = [e for e in results_7d if e["data"].get("status") == "error"]
        error_rate_7d = len(errors_7d) / len(results_7d) * 100 if results_7d else 0
        
        return {
            "generated_at": datetime.now().isoformat(),
            "period_30d": {
                "total_events": len(events_30d),
                "by_source": sources_30d,
                "by_event_type": event_types_30d,
                "error_rate": round(error_rate_30d, 2)
            },
            "period_7d": {
                "total_events": len(events_7d),
                "by_source": sources_7d,
                "by_event_type": event_types_7d,
                "error_rate": round(error_rate_7d, 2)
            },
            "latest_intents": latest_intents,
            "activity_trend": {
                "daily_avg_30d": round(len(events_30d) / 30, 2),
                "daily_avg_7d": round(len(events_7d) / 7, 2)
            }
        }
    
    def get_context_for_ai(self, days: int = 7) -> str:
        """
        AIが理解しやすい形式で文脈を文字列として返す
        
        Args:
            days: 分析対象の日数
        
        Returns:
            AI向けの文脈説明文字列
        """
        recent_changes = self.get_recent_changes(days=days)
        project_state = self.summarize_project_state()
        
        lines = []
        lines.append(f"# Resonant Engine - Project Context (Last {days} days)")
        lines.append("")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # サマリー
        lines.append("## Summary")
        lines.append("")
        summary = recent_changes["summary"]
        lines.append(f"- Total Events: {summary['total_events']}")
        lines.append(f"- Intents: {summary['intents_count']}")
        lines.append(f"- Actions: {summary['actions_count']}")
        lines.append(f"- Success Rate: {100 - project_state['period_7d']['error_rate']:.1f}%")
        lines.append("")
        
        # 最近の意図
        if recent_changes["intents"]:
            lines.append("## Recent Development Intentions")
            lines.append("")
            for intent in recent_changes["intents"][:5]:
                timestamp = intent["timestamp"][:19].replace("T", " ")
                lines.append(f"- [{timestamp}] {intent['intent']}")
                if intent.get("context"):
                    lines.append(f"  Context: {intent['context']}")
            lines.append("")
        
        # 最近のエラー
        if recent_changes["recent_errors"]:
            lines.append("## Recent Issues")
            lines.append("")
            for error in recent_changes["recent_errors"][:3]:
                timestamp = error["timestamp"][:19].replace("T", " ")
                error_msg = str(error["error"])[:100]
                lines.append(f"- [{timestamp}] {error['source']}: {error_msg}")
            lines.append("")
        
        # 活動トレンド
        lines.append("## Activity Trend")
        lines.append("")
        trend = project_state["activity_trend"]
        lines.append(f"- Daily Average (Last 7 days): {trend['daily_avg_7d']} events/day")
        lines.append(f"- Daily Average (Last 30 days): {trend['daily_avg_30d']} events/day")
        lines.append("")
        
        return "\n".join(lines)


# ============================================
# CLI実行
# ============================================

def main():
    """メイン処理"""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="Resonant Context API")
    parser.add_argument("command", choices=["recent", "spec", "summary", "ai"],
                       help="実行するコマンド")
    parser.add_argument("--days", type=int, default=7, help="分析対象の日数（デフォルト: 7）")
    parser.add_argument("--feature", type=str, help="機能名（specコマンド用）")
    parser.add_argument("--format", choices=["json", "text"], default="json",
                       help="出力形式（デフォルト: json）")
    
    args = parser.parse_args()
    
    api = ResonantContextAPI()
    
    if args.command == "recent":
        result = api.get_recent_changes(days=args.days)
        if args.format == "json":
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"Recent Changes (Last {args.days} days):")
            print(f"  Total Events: {result['summary']['total_events']}")
            print(f"  Intents: {result['summary']['intents_count']}")
            print(f"  Actions: {result['summary']['actions_count']}")
    
    elif args.command == "spec":
        if not args.feature:
            print("❌ --featureオプションが必要です")
            return
        result = api.get_spec_history(args.feature)
        if args.format == "json":
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"Spec History for '{args.feature}':")
            print(f"  Total Events: {result['total_events']}")
            for event in result['events'][:5]:
                print(f"  - {event['timestamp']}: {event['spec_name']}")
    
    elif args.command == "summary":
        result = api.summarize_project_state()
        if args.format == "json":
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("Project State Summary:")
            print(f"  Events (Last 7 days): {result['period_7d']['total_events']}")
            print(f"  Events (Last 30 days): {result['period_30d']['total_events']}")
            print(f"  Error Rate (Last 7 days): {result['period_7d']['error_rate']}%")
    
    elif args.command == "ai":
        result = api.get_context_for_ai(days=args.days)
        print(result)


if __name__ == "__main__":
    main()

