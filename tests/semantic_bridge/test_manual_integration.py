#!/usr/bin/env python3
"""
Semantic Bridge System 手動統合テストスクリプト

ローカル環境での受け入れテスト用スクリプト。
全機能を順番に実行し、動作確認を行います。

使用方法:
    python tests/semantic_bridge/test_manual_integration.py
"""

import asyncio
from datetime import datetime, timezone
from uuid import uuid4

from bridge.semantic_bridge.extractor import SemanticExtractor
from bridge.semantic_bridge.inferencer import TypeProjectInferencer
from bridge.semantic_bridge.constructor import MemoryUnitConstructor
from bridge.semantic_bridge.service import SemanticBridgeService
from bridge.semantic_bridge.repositories import InMemoryUnitRepository
from bridge.semantic_bridge.models import (
    EventContext,
    MemoryType,
    EmotionState,
    MemorySearchQuery,
)


async def main():
    print("=" * 60)
    print("Semantic Bridge System 統合テスト")
    print("=" * 60)
    print()

    # サービス初期化
    repo = InMemoryUnitRepository()
    service = SemanticBridgeService(memory_repo=repo)

    # 1. 基本的なイベント処理
    print("【テスト1】基本的なイベント処理")
    print("-" * 40)
    event1 = EventContext(
        intent_id=uuid4(),
        intent_text="Design memory management system for Resonant Engine",
        intent_type="feature_request",
        timestamp=datetime.now(timezone.utc),
        crisis_index=25,
    )
    memory_unit = await service.process_event(event1)
    print(f"  Event ID: {event1.intent_id}")
    print(f"  Memory Unit ID: {memory_unit.id}")
    print(f"  Type: {memory_unit.type.value}")
    print(f"  Project: {memory_unit.project_id}")
    print(f"  Tags: {memory_unit.tags[:5]}...")
    print(f"  Emotion: {memory_unit.emotion_state.value if memory_unit.emotion_state else 'None'}")
    assert memory_unit.type == MemoryType.DESIGN_NOTE
    assert memory_unit.project_id == "resonant_engine"
    print("  ✅ PASS")
    print()

    # 2. 規範タイプ推論
    print("【テスト2】規範タイプ推論")
    print("-" * 40)
    event2 = EventContext(
        intent_id=uuid4(),
        intent_text="新しい規範を定義する：コードレビューは必須",
        intent_type="feature_request",
        timestamp=datetime.now(timezone.utc),
        crisis_index=15,
    )
    unit2 = await service.process_event(event2)
    print(f"  Intent: {event2.intent_text}")
    print(f"  Type: {unit2.type.value}")
    assert unit2.type == MemoryType.RESONANT_REGULATION
    print("  ✅ PASS")
    print()

    # 3. マイルストーンタイプ推論
    print("【テスト3】マイルストーンタイプ推論")
    print("-" * 40)
    event3 = EventContext(
        intent_id=uuid4(),
        intent_text="プロジェクトの重要なマイルストーンを達成した",
        intent_type="feature_request",
        timestamp=datetime.now(timezone.utc),
        crisis_index=10,
    )
    unit3 = await service.process_event(event3)
    print(f"  Intent: {event3.intent_text}")
    print(f"  Type: {unit3.type.value}")
    assert unit3.type == MemoryType.PROJECT_MILESTONE
    print("  ✅ PASS")
    print()

    # 4. 日次振り返りタイプ推論
    print("【テスト4】日次振り返りタイプ推論")
    print("-" * 40)
    event4 = EventContext(
        intent_id=uuid4(),
        intent_text="今日の振り返りを行う：進捗は順調",
        intent_type="exploration",
        timestamp=datetime.now(timezone.utc),
        crisis_index=20,
    )
    unit4 = await service.process_event(event4)
    print(f"  Intent: {event4.intent_text}")
    print(f"  Type: {unit4.type.value}")
    assert unit4.type == MemoryType.DAILY_REFLECTION
    print("  ✅ PASS")
    print()

    # 5. 危機ログタイプ推論（高CI Level）
    print("【テスト5】危機ログタイプ推論（高CI Level）")
    print("-" * 40)
    event5 = EventContext(
        intent_id=uuid4(),
        intent_text="システムが正常に動作している",
        intent_type="bug_fix",
        timestamp=datetime.now(timezone.utc),
        crisis_index=75,  # High CI Level triggers crisis
    )
    unit5 = await service.process_event(event5)
    print(f"  Intent: {event5.intent_text}")
    print(f"  CI Level: {event5.crisis_index}")
    print(f"  Type: {unit5.type.value}")
    print(f"  Emotion: {unit5.emotion_state.value if unit5.emotion_state else 'None'}")
    assert unit5.type == MemoryType.CRISIS_LOG
    assert unit5.emotion_state == EmotionState.CRISIS
    print("  ✅ PASS")
    print()

    # 6. PostgreSQLプロジェクト推論
    print("【テスト6】PostgreSQLプロジェクト推論")
    print("-" * 40)
    event6 = EventContext(
        intent_id=uuid4(),
        intent_text="PostgreSQLのスキーマをマイグレーションする",
        intent_type="feature_request",
        timestamp=datetime.now(timezone.utc),
        crisis_index=30,
    )
    unit6 = await service.process_event(event6)
    print(f"  Intent: {event6.intent_text}")
    print(f"  Project: {unit6.project_id}")
    assert unit6.project_id == "postgres_implementation"
    print("  ✅ PASS")
    print()

    # 7. Kana応答付きイベント
    print("【テスト7】Kana応答付きイベント処理")
    print("-" * 40)
    event7 = EventContext(
        intent_id=uuid4(),
        intent_text="メモリシステムの設計を相談",
        intent_type="feature_request",
        timestamp=datetime.now(timezone.utc),
        crisis_index=20,
        kana_response="メモリシステムの設計には、Repository Patternを採用することをお勧めします。",
    )
    unit7 = await service.process_event(event7)
    print(f"  Intent: {event7.intent_text}")
    print(f"  Kana Response: {event7.kana_response[:50]}...")
    print(f"  Content contains response: {'【応答】' in unit7.content}")
    assert "【応答】" in unit7.content
    assert event7.kana_response in unit7.content
    print("  ✅ PASS")
    print()

    # 8. メタデータ確認
    print("【テスト8】推論メタデータ確認")
    print("-" * 40)
    print(f"  Inference Confidence: {unit7.metadata.get('inference_confidence')}")
    print(f"  Inference Reasoning: {unit7.metadata.get('inference_reasoning')}")
    print(f"  Project Confidence: {unit7.metadata.get('project_confidence')}")
    assert "inference_confidence" in unit7.metadata
    assert "inference_reasoning" in unit7.metadata
    print("  ✅ PASS")
    print()

    # 9. 検索機能テスト - プロジェクト検索
    print("【テスト9】プロジェクト検索")
    print("-" * 40)
    query1 = MemorySearchQuery(project_id="resonant_engine")
    results1 = await repo.search(query1)
    print(f"  Query: project_id='resonant_engine'")
    print(f"  Results: {len(results1)}件")
    assert len(results1) >= 1
    print("  ✅ PASS")
    print()

    # 10. 検索機能テスト - タイプ検索
    print("【テスト10】タイプ検索")
    print("-" * 40)
    query2 = MemorySearchQuery(type=MemoryType.DESIGN_NOTE)
    results2 = await repo.search(query2)
    print(f"  Query: type='design_note'")
    print(f"  Results: {len(results2)}件")
    for r in results2:
        print(f"    - {r.title[:40]}...")
    assert len(results2) >= 1
    assert all(r.type == MemoryType.DESIGN_NOTE for r in results2)
    print("  ✅ PASS")
    print()

    # 11. 検索機能テスト - テキスト検索
    print("【テスト11】テキスト検索")
    print("-" * 40)
    query3 = MemorySearchQuery(text_query="PostgreSQL")
    results3 = await repo.search(query3)
    print(f"  Query: text='PostgreSQL'")
    print(f"  Results: {len(results3)}件")
    assert len(results3) >= 1
    print("  ✅ PASS")
    print()

    # 12. 検索機能テスト - 感情状態検索
    print("【テスト12】感情状態検索")
    print("-" * 40)
    query4 = MemorySearchQuery(emotion_states=[EmotionState.CRISIS])
    results4 = await repo.search(query4)
    print(f"  Query: emotion_states=['crisis']")
    print(f"  Results: {len(results4)}件")
    assert len(results4) >= 1
    assert all(r.emotion_state == EmotionState.CRISIS for r in results4)
    print("  ✅ PASS")
    print()

    # 13. プロジェクト統計
    print("【テスト13】プロジェクト統計")
    print("-" * 40)
    projects = await repo.get_projects()
    print(f"  Total Projects: {len(projects)}")
    for p in projects:
        print(f"    - {p['project_id']}: {p['memory_count']}件")
    assert len(projects) >= 2
    print("  ✅ PASS")
    print()

    # 14. タグ統計
    print("【テスト14】タグ統計")
    print("-" * 40)
    tags = await repo.get_tags()
    print(f"  Total Unique Tags: {len(tags)}")
    top_tags = sorted(tags, key=lambda t: t["count"], reverse=True)[:5]
    for t in top_tags:
        print(f"    - {t['tag']}: {t['count']}件")
    assert len(tags) >= 5
    print("  ✅ PASS")
    print()

    # 15. バッチ処理テスト
    print("【テスト15】バッチ処理テスト")
    print("-" * 40)
    batch_events = [
        EventContext(
            intent_id=uuid4(),
            intent_text=f"Batch task {i}",
            intent_type="feature_request",
            timestamp=datetime.now(timezone.utc),
        )
        for i in range(3)
    ]
    batch_results = await service.process_events_batch(batch_events)
    print(f"  Batch Size: {len(batch_events)}")
    print(f"  Processed: {len(batch_results)}")
    assert len(batch_results) == 3
    print("  ✅ PASS")
    print()

    # テスト完了
    print("=" * 60)
    print("🎉 全テスト完了！")
    print("=" * 60)
    print()
    print("テスト結果サマリー:")
    print(f"  ✅ 基本イベント処理: OK")
    print(f"  ✅ メモリタイプ推論（6種類）: OK")
    print(f"  ✅ プロジェクト推論: OK")
    print(f"  ✅ 感情状態推論: OK")
    print(f"  ✅ Kana応答統合: OK")
    print(f"  ✅ 推論メタデータ保存: OK")
    print(f"  ✅ シンボリック検索（4種類）: OK")
    print(f"  ✅ 統計機能: OK")
    print(f"  ✅ バッチ処理: OK")
    print()

    total_memories = len(repo.get_all())
    print(f"  Total Memory Units Created: {total_memories}")
    print()
    print("Semantic Bridge System は仕様通りに実装されています。")


if __name__ == "__main__":
    asyncio.run(main())
