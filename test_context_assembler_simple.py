#!/usr/bin/env python3
"""Context Assembler 簡易機能テスト"""

import sys
sys.path.insert(0, '/app')

# TokenEstimatorの直接インポート（__init__.pyを回避）
from context_assembler.token_estimator import TokenEstimator

print("=" * 60)
print("Context Assembler - Sprint 5 受け入れテスト")
print("=" * 60)

# TC-05: トークン数推定テスト
print("\n[TC-05] トークン数推定テスト")
print("-" * 60)

te = TokenEstimator()

test_cases = [
    {
        "name": "単一メッセージ",
        "messages": [{"role": "user", "content": "Hello"}],
        "expected_min": 5,
        "expected_max": 20
    },
    {
        "name": "複数メッセージ",
        "messages": [
            {"role": "user", "content": "こんにちは"},
            {"role": "assistant", "content": "はい、何でしょうか？"},
            {"role": "user", "content": "天気を教えて"}
        ],
        "expected_min": 50,
        "expected_max": 100
    },
    {
        "name": "長文メッセージ",
        "messages": [{
            "role": "user",
            "content": "Resonant Engine は、人間とAIが呼吸のように情報を往復させる知性アーキテクチャです。" * 10
        }],
        "expected_min": 500,
        "expected_max": 1000
    }
]

passed = 0
failed = 0

for tc in test_cases:
    tokens = te.estimate(tc["messages"])
    expected_min = tc["expected_min"]
    expected_max = tc["expected_max"]
    
    if expected_min <= tokens <= expected_max:
        print(f"✅ PASS: {tc['name']}")
        print(f"   推定トークン数: {tokens} (範囲: {expected_min}-{expected_max})")
        passed += 1
    else:
        print(f"❌ FAIL: {tc['name']}")
        print(f"   推定トークン数: {tokens} (期待範囲: {expected_min}-{expected_max})")
        failed += 1

print("\n" + "=" * 60)
print(f"テスト結果: {passed} PASS / {failed} FAIL")
print("=" * 60)

# 終了コード
sys.exit(0 if failed == 0 else 1)
