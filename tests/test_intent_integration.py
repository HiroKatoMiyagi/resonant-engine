#!/usr/bin/env python3
"""
Intent処理フロー統合テスト
1. Intent作成（API経由）
2. デーモンによる自動処理
3. 結果確認
"""
import asyncio
import os
import requests
from pathlib import Path
import sys

import pytest

# プロジェクトルート追加
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from dashboard.backend.intent_processor_db import IntentProcessorDB

BASE_URL = "http://localhost:8000"
RUN_LEGACY_E2E = os.getenv("RUN_LEGACY_E2E") == "1"

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.skipif(
        not RUN_LEGACY_E2E,
        reason="Legacy integration flow requires RUN_LEGACY_E2E=1 with live services and Postgres.",
    ),
]

def print_section(title):
    """セクション区切り"""
    print(f"\n{'='*60}")
    print(f"📋 {title}")
    print('='*60)

async def test_intent_creation():
    """テスト1: IntentをDBに作成"""
    print_section("Test 1: Intent作成")
    
    processor = IntentProcessorDB()
    await processor.init_db()
    
    # Intent作成
    intent_id = await processor.create_intent(
        intent_type="review_spec",
        data={
            "spec_title": "ユーザー認証API仕様",
            "request": "セキュリティ観点でレビューしてください"
        },
        source="api"
    )
    
    print(f"✅ Intent作成完了: {intent_id}")
    await processor.close_db()
    
    return intent_id

async def test_intent_processing(intent_id):
    """テスト2: Intent処理"""
    print_section("Test 2: Intent処理")
    
    processor = IntentProcessorDB()
    await processor.init_db()
    
    # Intent処理
    success = await processor.process_intent(intent_id)
    
    if success:
        print(f"✅ Intent処理成功: {intent_id}")
    else:
        print(f"❌ Intent処理失敗: {intent_id}")
    
    await processor.close_db()
    return success

def test_api_intent_list():
    """テスト3: API経由でIntent一覧取得"""
    print_section("Test 3: API経由Intent一覧取得")
    
    try:
        response = requests.get(f"{BASE_URL}/api/intents?limit=5")
        if response.status_code == 200:
            intents = response.json()
            print(f"✅ Intent一覧取得成功: {len(intents)}件")
            for intent in intents:
                print(f"  - {intent['id'][:8]}... | {intent['type']} | {intent['status']}")
            return True
        else:
            print(f"❌ API呼び出し失敗: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("⚠️ APIサーバーが起動していません")
        print("  別ターミナルで: uvicorn dashboard.backend.main:app --reload")
        return False

async def test_full_flow():
    """フルフロー統合テスト"""
    print("\n🚀 Intent処理フロー統合テスト開始")
    print("="*60)
    
    results = []
    
    # Test 1: Intent作成
    intent_id = await test_intent_creation()
    results.append(("Intent作成", intent_id is not None))
    
    # 少し待機
    await asyncio.sleep(1)
    
    # Test 2: Intent処理
    if intent_id:
        success = await test_intent_processing(intent_id)
        results.append(("Intent処理", success))
    
    # Test 3: API経由確認
    api_success = test_api_intent_list()
    results.append(("API確認", api_success))
    
    # 結果サマリー
    print_section("テスト結果サマリー")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\n✨ Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 すべてのテストに合格しました！")
        return True
    else:
        print("\n⚠️ 一部のテストが失敗しました")
        return False

async def main():
    """メインエントリーポイント"""
    try:
        success = await test_full_flow()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
