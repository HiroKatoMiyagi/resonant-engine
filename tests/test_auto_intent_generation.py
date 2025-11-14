#!/usr/bin/env python3
"""
Message→Intent自動生成のテスト
"""
import asyncio
import requests
import json

API_BASE = "http://localhost:8000"

# テストメッセージパターン
TEST_MESSAGES = [
    # 正常系: Intent生成されるべき
    {
        "content": "このコードをレビューしてください",
        "sender": "test_user",
        "expected_intent_type": "review"
    },
    {
        "content": "ユーザー認証機能を実装してほしい",
        "sender": "test_user",
        "expected_intent_type": "create"
    },
    {
        "content": "バグを修正してください",
        "sender": "test_user",
        "expected_intent_type": "fix"
    },
    {
        "content": "WebSocketのテストをお願いします",
        "sender": "test_user",
        "expected_intent_type": "test"
    },
    {
        "content": "なぜエラーが発生するのか調査して",
        "sender": "test_user",
        "expected_intent_type": "debug"
    },
    # 異常系: Intent生成されないべき
    {
        "content": "こんにちは",
        "sender": "test_user",
        "expected_intent_type": None
    },
    {
        "content": "了解",
        "sender": "test_user",
        "expected_intent_type": None
    },
]

def test_auto_intent_generation():
    """Message→Intent自動生成のテスト"""
    print("🧪 Message→Intent 自動生成テスト開始\n")
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(TEST_MESSAGES, 1):
        print(f"[Test {i}/{len(TEST_MESSAGES)}] {test_case['content'][:30]}...")
        
        try:
            # メッセージを作成
            response = requests.post(
                f"{API_BASE}/api/messages",
                json={
                    "content": test_case["content"],
                    "sender": test_case["sender"]
                }
            )
            
            if response.status_code != 200:
                print(f"  ❌ API Error: {response.status_code}")
                failed += 1
                continue
            
            data = response.json()
            message_id = data.get("id")
            intent_id = data.get("intent_id")
            
            # Intent生成の期待値チェック
            if test_case["expected_intent_type"]:
                # Intent生成されるべき
                if not intent_id:
                    print(f"  ❌ Expected Intent but got None")
                    failed += 1
                    continue
                
                # Intentの詳細を取得
                intents_response = requests.get(f"{API_BASE}/api/intents?limit=1")
                if intents_response.status_code == 200:
                    intents = intents_response.json()
                    if intents:
                        latest_intent = intents[0]
                        intent_type = latest_intent.get("type")
                        
                        if intent_type == test_case["expected_intent_type"]:
                            print(f"  ✅ Intent auto-generated: {intent_type}")
                            print(f"     Message ID: {message_id}")
                            print(f"     Intent ID: {intent_id}")
                            passed += 1
                        else:
                            print(f"  ❌ Wrong Intent type: expected={test_case['expected_intent_type']}, got={intent_type}")
                            failed += 1
                    else:
                        print(f"  ❌ No Intent found")
                        failed += 1
                else:
                    print(f"  ❌ Failed to fetch Intent")
                    failed += 1
            else:
                # Intent生成されないべき
                if intent_id:
                    print(f"  ❌ Unexpected Intent generated: {intent_id}")
                    failed += 1
                else:
                    print(f"  ✅ No Intent generated (as expected)")
                    passed += 1
            
        except Exception as e:
            print(f"  ❌ Exception: {e}")
            failed += 1
        
        print()
    
    # 結果サマリー
    print("="*50)
    print(f"✅ Passed: {passed}/{len(TEST_MESSAGES)}")
    print(f"❌ Failed: {failed}/{len(TEST_MESSAGES)}")
    print("="*50)
    
    return passed == len(TEST_MESSAGES)

if __name__ == "__main__":
    success = test_auto_intent_generation()
    exit(0 if success else 1)
