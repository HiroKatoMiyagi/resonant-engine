#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Record Intent - 開発意図の記録ツール
-------------------------------------
intent_logger.py の後継
統一イベントストリームに意図を記録する

使い方:
  $ python utils/record_intent.py "Backlog同期機能のリアルタイム化"
  $ python utils/record_intent.py "Webhook受信のエラーハンドリング改善"
"""

import sys
from pathlib import Path

# utils/ からの import を可能にする
sys.path.append(str(Path(__file__).parent))
from resonant_event_stream import get_stream


def record_intent(intent_text: str, source: str = "user", context: str = ""):
    """
    開発意図をイベントストリームに記録
    
    Args:
        intent_text: 意図の内容
        source: 発信元（デフォルト: user）
        context: 追加のコンテキスト情報
    
    Returns:
        記録されたイベントID
    """
    stream = get_stream()
    
    data = {
        "intent": intent_text
    }
    
    if context:
        data["context"] = context
    
    event_id = stream.emit(
        event_type="intent",
        source=source,
        data=data,
        tags=["intent", "user_action"]
    )
    
    print(f"✅ 意図を記録しました")
    print(f"   Event ID: {event_id}")
    print(f"   Intent: {intent_text}")
    
    return event_id


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使い方: python utils/record_intent.py <意図のテキスト> [コンテキスト]")
        print()
        print("例:")
        print("  python utils/record_intent.py 'Backlog同期機能のリアルタイム化'")
        print("  python utils/record_intent.py 'エラーハンドリング改善' 'Webhook受信時のタイムアウト対策'")
        sys.exit(1)
    
    intent = sys.argv[1]
    context = sys.argv[2] if len(sys.argv) > 2 else ""
    
    record_intent(intent, context=context)

