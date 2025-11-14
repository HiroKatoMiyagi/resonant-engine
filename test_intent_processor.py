#!/usr/bin/env python3
"""
Intent Processor テストスクリプト
環境変数を直接読み込んでテスト
"""
import os
import sys
from pathlib import Path

# .envファイルを読み込む
env_file = Path("/Users/zero/Projects/resonant-engine/.env")
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

# IntentProcessorをインポートしてテスト
sys.path.insert(0, str(Path("/Users/zero/Projects/resonant-engine/dashboard/backend")))

from intent_processor import IntentProcessor

print("=" * 50)
print("Intent Processor API接続テスト")
print("=" * 50)

# APIキーの確認
api_key = os.environ.get("ANTHROPIC_API_KEY", "")
print(f"✅ API Key loaded: {api_key[:20]}..." if api_key else "❌ API Key not found")

# IntentProcessorの初期化
processor = IntentProcessor()

# Intentが存在するか確認
intent_data = processor.read_intent()
if intent_data:
    print(f"✅ Intent found: {intent_data}")
    
    # Kanaを呼び出してテスト
    print("\n🔄 Calling Kana (Claude API)...")
    response = processor.call_kana(intent_data)
    
    if response:
        print(f"\n✅ Success! Response received ({len(response)} chars)")
        print(f"\n📝 Response preview:")
        print(response[:200] + "..." if len(response) > 200 else response)
    else:
        print("\n❌ Failed to get response")
else:
    print("❌ No intent file found")

print("\n" + "=" * 50)
