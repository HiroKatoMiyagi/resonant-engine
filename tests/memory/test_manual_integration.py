#!/usr/bin/env python3
"""
Memory Management System 手動統合テストスクリプト

ローカル環境での受け入れテスト用スクリプト。
全機能を順番に実行し、動作確認を行います。

使用方法:
    python tests/memory/test_manual_integration.py
"""

import asyncio
from bridge.memory.service import MemoryManagementService
from bridge.memory.in_memory_repositories import (
    InMemorySessionRepository,
    InMemoryIntentRepository,
    InMemoryResonanceRepository,
    InMemoryAgentContextRepository,
    InMemoryChoicePointRepository,
    InMemoryBreathingCycleRepository,
    InMemorySnapshotRepository,
)
from bridge.memory.models import (
    AgentType,
    BreathingPhase,
    Choice,
    IntentType,
    ResonanceState,
    SessionStatus,
    SnapshotType,
)


async def main():
    # サービス初期化
    service = MemoryManagementService(
        session_repo=InMemorySessionRepository(),
        intent_repo=InMemoryIntentRepository(),
        resonance_repo=InMemoryResonanceRepository(),
        agent_context_repo=InMemoryAgentContextRepository(),
        choice_point_repo=InMemoryChoicePointRepository(),
        breathing_cycle_repo=InMemoryBreathingCycleRepository(),
        snapshot_repo=InMemorySnapshotRepository(),
    )

    print("=" * 60)
    print("Memory Management System 統合テスト")
    print("=" * 60)
    print()

    # 1. セッション開始
    print("【テスト1】セッション開始")
    print("-" * 40)
    session = await service.start_session("hiroaki", {"client": "test", "version": "1.0"})
    print(f"  Session ID: {session.id}")
    print(f"  User ID: {session.user_id}")
    print(f"  Status: {session.status.value}")
    print(f"  Started At: {session.started_at}")
    print(f"  Metadata: {session.metadata}")
    assert session.status == SessionStatus.ACTIVE
    print("  ✅ PASS")
    print()

    # 2. Intent記録（呼吸フェーズ1: 吸う）
    print("【テスト2】Intent記録（呼吸フェーズ1: 吸う）")
    print("-" * 40)
    parent_intent = await service.record_intent(
        session.id,
        "Memory Management System実装",
        IntentType.FEATURE_REQUEST,
        priority=9,
        metadata={"source": "sprint_spec", "estimated_days": 5},
    )
    print(f"  Intent ID: {parent_intent.id}")
    print(f"  Text: {parent_intent.intent_text}")
    print(f"  Type: {parent_intent.intent_type.value}")
    print(f"  Priority: {parent_intent.priority}")
    print(f"  Status: {parent_intent.status.value}")
    assert parent_intent.priority == 9
    assert parent_intent.status.value == "pending"
    print("  ✅ PASS")
    print()

    # 3. 子Intent作成（階層構造テスト）
    print("【テスト3】子Intent作成（階層構造）")
    print("-" * 40)
    child_intent = await service.record_intent(
        session.id,
        "PostgreSQLスキーマ設計",
        IntentType.FEATURE_REQUEST,
        parent_intent_id=parent_intent.id,
        priority=8,
    )
    print(f"  Child Intent ID: {child_intent.id}")
    print(f"  Parent Intent ID: {child_intent.parent_intent_id}")
    print(f"  Text: {child_intent.intent_text}")
    assert child_intent.parent_intent_id == parent_intent.id
    print("  ✅ PASS")
    print()

    # 4. Resonance記録（呼吸フェーズ2: 共鳴）
    print("【テスト4】Resonance記録（呼吸フェーズ2: 共鳴）")
    print("-" * 40)
    resonance = await service.record_resonance(
        session.id,
        ResonanceState.ALIGNED,
        0.92,
        ["yuno", "kana", "tsumu"],
        intent_id=parent_intent.id,
        pattern_type="full_layer_alignment",
        duration_ms=1500,
    )
    print(f"  Resonance ID: {resonance.id}")
    print(f"  State: {resonance.state.value}")
    print(f"  Intensity: {resonance.intensity}")
    print(f"  Agents: {resonance.agents}")
    print(f"  Pattern: {resonance.pattern_type}")
    print(f"  Duration: {resonance.duration_ms}ms")
    assert resonance.intensity == 0.92
    assert resonance.agents == ["yuno", "kana", "tsumu"]
    print("  ✅ PASS")
    print()

    # 5. ChoicePoint作成（呼吸フェーズ3: 構造化）
    print("【テスト5】ChoicePoint作成（呼吸フェーズ3: 構造化）")
    print("-" * 40)
    choice_point = await service.create_choice_point(
        session.id,
        parent_intent.id,
        "PostgreSQL vs SQLite: どちらを選択すべきか？",
        [
            Choice(
                id="choice_pg",
                description="PostgreSQL: フル機能、本番環境向け",
                implications={
                    "pros": ["JSONB対応", "並行処理", "スケーラビリティ"],
                    "cons": ["セットアップ複雑", "リソース消費"],
                },
            ),
            Choice(
                id="choice_sqlite",
                description="SQLite: シンプル、軽量",
                implications={
                    "pros": ["設定不要", "低リソース"],
                    "cons": ["並行性制限", "JSONB非対応"],
                },
            ),
        ],
    )
    print(f"  ChoicePoint ID: {choice_point.id}")
    print(f"  Question: {choice_point.question}")
    print(f"  Number of Choices: {len(choice_point.choices)}")
    print(f"  Selected Choice: {choice_point.selected_choice_id} (未決定)")
    assert choice_point.selected_choice_id is None
    print("  ✅ PASS")
    print()

    # 6. Choice決定
    print("【テスト6】Choice決定")
    print("-" * 40)
    decided = await service.decide_choice(
        choice_point.id,
        "choice_pg",
        "Yuno評価A+。JSONB、並行性、将来性を考慮し、PostgreSQLを選択。"
    )
    print(f"  Selected Choice ID: {decided.selected_choice_id}")
    print(f"  Decided At: {decided.decided_at}")
    print(f"  Rationale: {decided.decision_rationale}")
    assert decided.selected_choice_id == "choice_pg"
    assert decided.decided_at is not None
    print("  ✅ PASS")
    print()

    # 7. AgentContext保存（呼吸フェーズ4: 再内省）
    print("【テスト7】AgentContext保存（呼吸フェーズ4: 再内省）")
    print("-" * 40)
    contexts = {}
    for agent_type in [AgentType.YUNO, AgentType.KANA, AgentType.TSUMU]:
        context = await service.save_agent_context(
            session.id,
            agent_type,
            {
                "focus": "Memory Management System",
                "current_decisions": ["PostgreSQL選択"],
                "insights": [f"{agent_type.value}層固有の洞察"],
                "pending_questions": ["パフォーマンス最適化は？"],
            },
            intent_id=parent_intent.id,
        )
        contexts[agent_type.value] = context
        print(f"  {agent_type.value.upper()}: version={context.version}, id={context.id}")
    assert len(contexts) == 3
    print("  ✅ PASS")
    print()

    # 8. AgentContextバージョニングテスト
    print("【テスト8】AgentContextバージョニング")
    print("-" * 40)
    v2_context = await service.save_agent_context(
        session.id,
        AgentType.KANA,
        {
            "focus": "Memory Management System",
            "current_decisions": ["PostgreSQL選択", "Repository Pattern採用"],
            "insights": ["バージョン2の洞察"],
        },
    )
    print(f"  Kana Context v2: version={v2_context.version}")
    latest = await service.get_latest_agent_context(session.id, AgentType.KANA)
    print(f"  Latest Version: {latest.version}")
    assert v2_context.version == 2
    assert latest.id == v2_context.id
    print("  ✅ PASS")
    print()

    # 9. BreathingCycle管理
    print("【テスト9】BreathingCycle管理（全6フェーズ）")
    print("-" * 40)
    phases = [
        (BreathingPhase.INTAKE, {"action": "intent_recording"}),
        (BreathingPhase.RESONANCE, {"action": "resonance_recording"}),
        (BreathingPhase.STRUCTURING, {"action": "choice_creation"}),
        (BreathingPhase.RE_REFLECTION, {"action": "context_update"}),
        (BreathingPhase.IMPLEMENTATION, {"action": "schema_design"}),
        (BreathingPhase.RESONANCE_EXPANSION, {"action": "session_continuation"}),
    ]
    for phase, data in phases:
        cycle = await service.start_breathing_phase(
            session.id, phase, intent_id=parent_intent.id, phase_data=data
        )
        completed = await service.complete_breathing_phase(
            cycle.id, success=True, phase_data={"outcome": f"{phase.value}_completed"}
        )
        print(f"  {phase.value}: started -> completed (success={completed.success})")
    cycles = await service.list_session_breathing_cycles(session.id)
    assert len(cycles) == 6
    print(f"  Total Cycles: {len(cycles)}")
    print("  ✅ PASS")
    print()

    # 10. Snapshot作成（時間軸保全）
    print("【テスト10】Snapshot作成（時間軸保全）")
    print("-" * 40)
    snapshot = await service.create_snapshot(
        session.id,
        SnapshotType.MILESTONE,
        description="Memory Management System実装完了マイルストーン",
        tags=["memory", "milestone", "sprint4"],
    )
    print(f"  Snapshot ID: {snapshot.id}")
    print(f"  Type: {snapshot.snapshot_type.value}")
    print(f"  Description: {snapshot.description}")
    print(f"  Tags: {snapshot.tags}")
    print(f"  Snapshot Data Keys: {list(snapshot.snapshot_data.keys())}")
    assert "session" in snapshot.snapshot_data
    assert "intents" in snapshot.snapshot_data
    assert "resonances" in snapshot.snapshot_data
    assert "agent_contexts" in snapshot.snapshot_data
    assert "choice_points" in snapshot.snapshot_data
    assert "breathing_cycles" in snapshot.snapshot_data
    print("  ✅ PASS")
    print()

    # 11. Snapshotからの復元
    print("【テスト11】Snapshot復元")
    print("-" * 40)
    restored_data = await service.restore_from_snapshot(snapshot.id)
    print(f"  Restored Session ID: {restored_data['session']['id']}")
    print(f"  Restored Intents: {len(restored_data['intents'])}")
    print(f"  Restored Resonances: {len(restored_data['resonances'])}")
    print(f"  Restored Contexts: {len(restored_data['agent_contexts'])}")
    print(f"  Restored Choice Points: {len(restored_data['choice_points'])}")
    print(f"  Restored Breathing Cycles: {len(restored_data['breathing_cycles'])}")
    assert len(restored_data["intents"]) == 2
    print("  ✅ PASS")
    print()

    # 12. セッションサマリー
    print("【テスト12】セッションサマリー")
    print("-" * 40)
    summary = await service.get_session_summary(session.id)
    print(f"  Total Intents: {summary['total_intents']}")
    print(f"  Completed Intents: {summary['completed_intents']}")
    print(f"  Resonance Events: {summary['resonance_events']}")
    print(f"  Choice Points: {summary['choice_points']}")
    print(f"  Breathing Cycles: {summary['breathing_cycles']}")
    print(f"  Avg Intensity: {summary['avg_intensity']:.2f}")
    assert summary["total_intents"] == 2
    assert summary["resonance_events"] == 1
    assert summary["breathing_cycles"] == 6
    print("  ✅ PASS")
    print()

    # 13. Intent完了
    print("【テスト13】Intent完了")
    print("-" * 40)
    completed_intent = await service.complete_intent(
        parent_intent.id,
        {
            "implementation": "全機能実装完了",
            "learnings": ["Repository Pattern", "Pydanticバリデーション", "呼吸サイクルマッピング"],
            "metrics": {"lines_of_code": 5651, "test_cases": 72},
        },
    )
    print(f"  Intent ID: {completed_intent.id}")
    print(f"  Status: {completed_intent.status.value}")
    print(f"  Completed At: {completed_intent.completed_at}")
    print(f"  Outcome: {completed_intent.outcome}")
    assert completed_intent.status.value == "completed"
    assert completed_intent.completed_at is not None
    print("  ✅ PASS")
    print()

    # 14. セッション継続性テスト
    print("【テスト14】セッション継続性（呼吸フェーズ6: 共鳴拡大）")
    print("-" * 40)
    # セッションを一時停止
    await service.update_session_status(session.id, SessionStatus.PAUSED)
    print(f"  Session paused")

    # セッション継続
    continued = await service.continue_session(session.id)
    print(f"  Session Status: {continued['session'].status.value}")
    print(f"  Agent Contexts: {list(continued['agent_contexts'].keys())}")
    print(f"  Last Intent: {continued['last_intent'].intent_text}")
    print(f"  Pending Choices: {len(continued['pending_choices'])}")
    print(f"  Current Phase: {continued['current_breathing_phase']}")
    assert continued["session"].status == SessionStatus.ACTIVE
    assert "kana" in continued["agent_contexts"]
    assert "yuno" in continued["agent_contexts"]
    assert "tsumu" in continued["agent_contexts"]
    print("  ✅ PASS")
    print()

    # 15. 検索機能テスト
    print("【テスト15】Intent検索")
    print("-" * 40)
    search_results = await service.search_intents(session.id, "PostgreSQL")
    print(f"  Search Query: 'PostgreSQL'")
    print(f"  Results: {len(search_results)}件")
    for result in search_results:
        print(f"    - {result.intent_text}")
    assert len(search_results) >= 1
    print("  ✅ PASS")
    print()

    # テスト完了
    print("=" * 60)
    print("🎉 全テスト完了！")
    print("=" * 60)
    print()
    print("テスト結果サマリー:")
    print(f"  ✅ セッション管理: OK")
    print(f"  ✅ Intent管理（階層構造含む）: OK")
    print(f"  ✅ Resonance記録: OK")
    print(f"  ✅ ChoicePoint管理（選択肢保持）: OK")
    print(f"  ✅ AgentContextバージョニング: OK")
    print(f"  ✅ BreathingCycle全6フェーズ: OK")
    print(f"  ✅ Snapshot作成・復元（時間軸保全）: OK")
    print(f"  ✅ セッション継続性: OK")
    print(f"  ✅ Intent検索: OK")
    print()
    print("Memory Management System は仕様通りに実装されています。")


if __name__ == "__main__":
    asyncio.run(main())
