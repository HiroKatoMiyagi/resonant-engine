"""
Sprint 4.5: 統合テストスクリプト
Intent Bridge全体の動作確認
"""
import asyncio
from intent_classifier import IntentClassifier
from context_loader import ContextLoader
from claude_code_client import ClaudeCodeClient


async def test_full_integration():
    """全コンポーネント統合テスト"""

    print("=" * 70)
    print("Sprint 4.5: 統合テスト開始")
    print("=" * 70)

    # テストIntent
    test_intents = [
        {
            "description": "Sprint 4.5のClaude Code Client実装を完了させて。Sprint 4も参考に",
            "expected_type": "code_execution"
        },
        {
            "description": "bridge/intent_bridge.pyにログ追加とエラーハンドリング改善",
            "expected_type": "code_execution"
        },
        {
            "description": "PostgreSQLのパフォーマンスチューニングについて教えて",
            "expected_type": "chat"
        }
    ]

    for i, test in enumerate(test_intents, 1):
        print(f"\n{'='*70}")
        print(f"テストケース {i}: {test['description'][:50]}...")
        print('-' * 70)

        description = test['description']

        # 1. Intent分類
        print("\n[1. Intent分類]")
        classifier = IntentClassifier()
        intent_type = classifier.classify(description)
        confidence = classifier.get_confidence(description)

        status = "✅" if intent_type == test['expected_type'] else "❌"
        print(f"{status} 分類結果: {intent_type} (期待: {test['expected_type']})")
        print(f"   信頼度: {confidence:.2f}")

        if intent_type != test['expected_type']:
            print("   ⚠️  分類エラー！")
            continue

        # 2. コンテキストロード
        print("\n[2. コンテキストロード]")
        loader = ContextLoader()
        context = loader.load_context_for_intent(description, max_files=10)

        print(f"✅ ファイル数: {len(context['files'])}")
        print(f"   関連Sprint: {context['related_sprints']}")
        print(f"   サマリー:")
        for line in context['context_summary'].split('\n')[:5]:
            print(f"     {line}")

        # 3. Claude Code実行（code_executionの場合のみ）
        if intent_type == 'code_execution':
            print("\n[3. Claude Code実行]")
            client = ClaudeCodeClient(workspace_mode='repository')

            try:
                result = await client.execute_task(
                    task_description=description,
                    context=context,
                    timeout=10
                )

                print(f"✅ 実行成功")
                print(f"   Session ID: {result['session_id'][:8]}")
                print(f"   Success: {result['success']}")
                print(f"   Branch: {result.get('branch', 'N/A')}")
                print(f"   Context Files: {len(result.get('context_files_used', []))}個")

            except Exception as e:
                print(f"❌ 実行エラー: {e}")
        else:
            print("\n[3. Claude API実行（スキップ）]")
            print("   ※ チャットタイプのため、実際のAPI呼び出しは省略")

        print(f"\n{'✅ テストケース完了':^70}")

    print(f"\n{'='*70}")
    print("全テスト完了")
    print("=" * 70)


async def test_db_memory_mock():
    """DB記憶統合のモックテスト"""
    print("\n" + "=" * 70)
    print("DB記憶統合テスト（モック）")
    print("=" * 70)

    # 模擬的な過去Intent
    mock_memories = [
        {
            'id': 'abc-123',
            'description': 'Sprint 4のIntent Bridge実装',
            'status': 'completed',
            'result': {
                'type': 'code_execution',
                'files_created': ['bridge/intent_bridge.py'],
                'approach': 'asyncpg + LISTEN/NOTIFY使用'
            },
            'processed_at': '2025-11-17T10:30:00Z'
        }
    ]

    print("\n模擬DB記憶:")
    for memory in mock_memories:
        print(f"  - Intent: {memory['description']}")
        print(f"    Status: {memory['status']}")
        print(f"    Result: {memory['result']}")

    print("\n✅ DB記憶統合モックテスト完了")


if __name__ == '__main__':
    # 統合テスト実行
    asyncio.run(test_full_integration())

    # DB記憶テスト
    asyncio.run(test_db_memory_mock())

    print("\n" + "=" * 70)
    print("全テストスイート完了")
    print("=" * 70)
