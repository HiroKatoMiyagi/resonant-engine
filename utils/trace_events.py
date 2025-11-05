#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trace Events - イベントストリーム可視化ツール
--------------------------------------------
統一イベントストリームを検索・追跡するCLIツール

使い方:
  # 最近のイベントを表示
  $ python utils/trace_events.py recent

  # 特定の仮説に関連するイベントを表示
  $ python utils/trace_events.py hypothesis HYP-20251105-143000-abc123

  # 因果関係を遡る
  $ python utils/trace_events.py causality EVT-20251105-143530-def456

  # 特定の発生源のイベントを検索
  $ python utils/trace_events.py source observer_daemon

  # タグでフィルタ
  $ python utils/trace_events.py tag git
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

# utils/ からの import を可能にする
sys.path.append(str(Path(__file__).parent))
from resonant_event_stream import get_stream


def format_event(event: dict, indent: int = 0) -> str:
    """イベントを人間が読みやすい形式でフォーマット"""
    prefix = "  " * indent
    timestamp = event['timestamp'][:19]  # ISO8601の日時部分のみ
    event_type = event['event_type']
    source = event['source']
    
    # イベント種別の絵文字
    emoji_map = {
        "intent": "💡",
        "action": "⚡",
        "result": "✅" if event.get('data', {}).get('status') == 'success' else "❌",
        "observation": "👁️",
        "hypothesis": "🧠"
    }
    emoji = emoji_map.get(event_type, "📌")
    
    lines = [
        f"{prefix}{emoji} [{timestamp}] {event_type.upper()} from {source}",
        f"{prefix}   Event ID: {event['event_id']}"
    ]
    
    # 親イベントがあれば表示
    if event.get('parent_event_id'):
        lines.append(f"{prefix}   Parent: {event['parent_event_id']}")
    
    # 関連仮説があれば表示
    if event.get('related_hypothesis_id'):
        lines.append(f"{prefix}   Hypothesis: {event['related_hypothesis_id']}")
    
    # データを表示
    data = event.get('data', {})
    if data:
        lines.append(f"{prefix}   Data:")
        for key, value in data.items():
            # 長すぎる値は切り詰める
            if isinstance(value, str) and len(value) > 100:
                value = value[:100] + "..."
            lines.append(f"{prefix}     {key}: {value}")
    
    # タグを表示
    if event.get('tags'):
        lines.append(f"{prefix}   Tags: {', '.join(event['tags'])}")
    
    return "\n".join(lines)


def cmd_recent(limit: int = 20):
    """最近のイベントを表示"""
    stream = get_stream()
    events = stream.query(limit=limit)
    
    if not events:
        print("📭 イベントが見つかりませんでした")
        return
    
    print(f"📊 最近の{len(events)}件のイベント:\n")
    for event in events:
        print(format_event(event))
        print()


def cmd_hypothesis(hypothesis_id: str):
    """特定の仮説に関連する全イベントを表示"""
    stream = get_stream()
    timeline = stream.get_timeline(hypothesis_id)
    
    if not timeline:
        print(f"📭 仮説 {hypothesis_id} に関連するイベントが見つかりませんでした")
        return
    
    print(f"🧠 仮説 {hypothesis_id} のタイムライン:\n")
    for event in timeline:
        print(format_event(event))
        print()


def cmd_causality(event_id: str):
    """因果関係を遡って表示"""
    stream = get_stream()
    chain = stream.trace_causality(event_id)
    
    if not chain:
        print(f"📭 イベント {event_id} の因果関係が見つかりませんでした")
        return
    
    print(f"🔗 イベント {event_id} の因果関係チェーン:\n")
    print("原因 → 結果の流れ:")
    print()
    
    for i, event in enumerate(chain):
        if i > 0:
            print("  ↓")
        print(format_event(event))
        print()


def cmd_source(source_name: str, limit: int = 20):
    """特定の発生源からのイベントを検索"""
    stream = get_stream()
    events = stream.query(source=source_name, limit=limit)
    
    if not events:
        print(f"📭 発生源 {source_name} からのイベントが見つかりませんでした")
        return
    
    print(f"📡 発生源 {source_name} からの{len(events)}件のイベント:\n")
    for event in events:
        print(format_event(event))
        print()


def cmd_tag(tag: str, limit: int = 20):
    """特定のタグでフィルタ"""
    stream = get_stream()
    events = stream.query(tags=[tag], limit=limit)
    
    if not events:
        print(f"📭 タグ '{tag}' を持つイベントが見つかりませんでした")
        return
    
    print(f"🏷️ タグ '{tag}' を持つ{len(events)}件のイベント:\n")
    for event in events:
        print(format_event(event))
        print()


def cmd_summary(days: int = 7):
    """指定日数の活動サマリーを表示"""
    stream = get_stream()
    since = datetime.now() - timedelta(days=days)
    events = stream.query(since=since, limit=1000)
    
    if not events:
        print(f"📭 過去{days}日間のイベントが見つかりませんでした")
        return
    
    # イベント種別ごとに集計
    by_type = {}
    by_source = {}
    hypotheses = []
    
    for event in events:
        event_type = event['event_type']
        source = event['source']
        
        by_type[event_type] = by_type.get(event_type, 0) + 1
        by_source[source] = by_source.get(source, 0) + 1
        
        if event_type == "hypothesis":
            hypotheses.append(event)
    
    print(f"📈 過去{days}日間の活動サマリー")
    print(f"   総イベント数: {len(events)}件\n")
    
    print("イベント種別:")
    for event_type, count in sorted(by_type.items(), key=lambda x: -x[1]):
        print(f"  - {event_type}: {count}件")
    
    print("\n発生源:")
    for source, count in sorted(by_source.items(), key=lambda x: -x[1]):
        print(f"  - {source}: {count}件")
    
    if hypotheses:
        print(f"\n🧠 記録された仮説: {len(hypotheses)}件")
        for hyp in hypotheses[:5]:  # 最新5件のみ表示
            data = hyp.get('data', {})
            print(f"  - {data.get('hypothesis_id')}: {data.get('intent')}")


def main():
    if len(sys.argv) < 2:
        print("""使い方: python utils/trace_events.py <コマンド> [引数]

コマンド:
  recent [件数]              最近のイベントを表示 (デフォルト: 20件)
  hypothesis <仮説ID>        特定の仮説に関連するイベントを表示
  causality <イベントID>     因果関係を遡って表示
  source <発生源名> [件数]   特定の発生源からのイベントを検索
  tag <タグ名> [件数]        特定のタグでフィルタ
  summary [日数]             活動サマリーを表示 (デフォルト: 7日間)

例:
  python utils/trace_events.py recent
  python utils/trace_events.py recent 50
  python utils/trace_events.py hypothesis HYP-20251105-143000-abc123
  python utils/trace_events.py causality EVT-20251105-143530-def456
  python utils/trace_events.py source observer_daemon
  python utils/trace_events.py tag git
  python utils/trace_events.py summary 14
""")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "recent":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        cmd_recent(limit)
    
    elif command == "hypothesis":
        if len(sys.argv) < 3:
            print("エラー: 仮説IDを指定してください")
            sys.exit(1)
        cmd_hypothesis(sys.argv[2])
    
    elif command == "causality":
        if len(sys.argv) < 3:
            print("エラー: イベントIDを指定してください")
            sys.exit(1)
        cmd_causality(sys.argv[2])
    
    elif command == "source":
        if len(sys.argv) < 3:
            print("エラー: 発生源名を指定してください")
            sys.exit(1)
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 20
        cmd_source(sys.argv[2], limit)
    
    elif command == "tag":
        if len(sys.argv) < 3:
            print("エラー: タグ名を指定してください")
            sys.exit(1)
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 20
        cmd_tag(sys.argv[2], limit)
    
    elif command == "summary":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        cmd_summary(days)
    
    else:
        print(f"エラー: 不明なコマンド '{command}'")
        print("使い方: python utils/trace_events.py --help")
        sys.exit(1)


if __name__ == "__main__":
    main()

