#!/usr/bin/env python3
"""
Resonant Engine API テストスクリプト
"""
import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

def print_response(title: str, response: requests.Response):
    """レスポンスを整形して表示"""
    print(f"\n{'='*60}")
    print(f"📡 {title}")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    try:
        data = response.json()
        print(f"Response:\n{json.dumps(data, indent=2, ensure_ascii=False)}")
    except:
        print(f"Response: {response.text}")
    print()

def test_health():
    """ヘルスチェック"""
    response = requests.get(f"{BASE_URL}/health")
    print_response("Health Check", response)
    return response.status_code == 200

def test_create_message():
    """メッセージ作成テスト"""
    payload = {
        "content": "API設計レビューをお願いします",
        "sender": "user"
    }
    response = requests.post(f"{BASE_URL}/api/messages", json=payload)
    print_response("Create Message", response)
    
    if response.status_code == 200:
        return response.json()["id"]
    return None

def test_get_messages():
    """メッセージ一覧取得テスト"""
    response = requests.get(f"{BASE_URL}/api/messages?limit=10")
    print_response("Get Messages", response)
    return response.status_code == 200

def test_create_spec():
    """仕様書作成テスト"""
    payload = {
        "title": "ユーザー認証API仕様",
        "content": "## 概要\n認証APIの設計仕様書です。\n\n## エンドポイント\n- POST /api/auth/login\n- POST /api/auth/logout",
        "status": "draft"
    }
    response = requests.post(f"{BASE_URL}/api/specs", json=payload)
    print_response("Create Spec", response)
    
    if response.status_code == 200:
        return response.json()["id"]
    return None

def test_get_specs():
    """仕様書一覧取得テスト"""
    response = requests.get(f"{BASE_URL}/api/specs?limit=10")
    print_response("Get Specs", response)
    return response.status_code == 200

def test_get_spec(spec_id: str):
    """仕様書取得テスト"""
    response = requests.get(f"{BASE_URL}/api/specs/{spec_id}")
    print_response(f"Get Spec (ID: {spec_id})", response)
    return response.status_code == 200

def test_get_intents():
    """Intent一覧取得テスト"""
    response = requests.get(f"{BASE_URL}/api/intents?limit=10")
    print_response("Get Intents", response)
    return response.status_code == 200

def test_get_stats():
    """統計情報取得テスト"""
    response = requests.get(f"{BASE_URL}/api/stats")
    print_response("Get Stats", response)
    return response.status_code == 200

def main():
    """全テスト実行"""
    print("🚀 Resonant Engine API Test Suite")
    print("="*60)
    
    results = []
    
    # 1. ヘルスチェック
    results.append(("Health Check", test_health()))
    
    # 2. メッセージ作成
    message_id = test_create_message()
    results.append(("Create Message", message_id is not None))
    
    # 3. メッセージ一覧
    results.append(("Get Messages", test_get_messages()))
    
    # 4. 仕様書作成
    spec_id = test_create_spec()
    results.append(("Create Spec", spec_id is not None))
    
    # 5. 仕様書一覧
    results.append(("Get Specs", test_get_specs()))
    
    # 6. 仕様書取得
    if spec_id:
        results.append(("Get Spec", test_get_spec(spec_id)))
    
    # 7. Intent一覧
    results.append(("Get Intents", test_get_intents()))
    
    # 8. 統計情報
    results.append(("Get Stats", test_get_stats()))
    
    # 結果サマリー
    print("\n" + "="*60)
    print("📊 Test Results Summary")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\n✨ Total: {passed}/{total} tests passed")
    print("="*60)
    
    return passed == total

if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to API server")
        print("Please make sure the server is running on http://localhost:8000")
        exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        exit(1)
