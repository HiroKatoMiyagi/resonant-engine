#!/usr/bin/env python3
"""
WebSocketリアルタイム通知のテスト
"""
import asyncio
import asyncpg
import json
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
import os

load_dotenv(ROOT / ".env")
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://resonant@localhost:5432/resonant")

async def test_notify():
    """PostgreSQL NOTIFYトリガーのテスト"""
    print("🧪 WebSocket NOTIFY テスト開始...")
    
    # データベース接続
    conn = await asyncpg.connect(DATABASE_URL)
    
    try:
        # メッセージを作成（トリガーでNOTIFYが発火）
        print("\n📨 メッセージを作成中...")
        result = await conn.fetchrow("""
            INSERT INTO messages (sender, content, thread_id)
            VALUES ($1, $2, $3)
            RETURNING id, created_at
        """, "test", "WebSocketリアルタイムテスト", None)
        
        print(f"✅ メッセージ作成完了: ID={result['id']}")
        print(f"   → WebSocketクライアントに通知が送信されているはずです")
        
        # Intent作成もテスト
        print("\n📨 Intentを作成中...")
        intent_result = await conn.fetchrow("""
            INSERT INTO intents (type, status, data)
            VALUES ($1, $2, $3)
            RETURNING id, created_at
        """, "test_intent", "pending", json.dumps({"test": "WebSocket"}))
        
        print(f"✅ Intent作成完了: ID={intent_result['id']}")
        print(f"   → WebSocketクライアントに通知が送信されているはずです")
        
        print("\n🎯 テスト完了！")
        print("💡 ブラウザの開発者ツールでWebSocketメッセージを確認してください")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(test_notify())
