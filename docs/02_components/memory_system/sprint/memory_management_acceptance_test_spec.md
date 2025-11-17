# Memory Management System 受け入れテスト仕様書

**作成日**: 2025-11-17
**バージョン**: 1.0.0
**対象システム**: Resonant Engine Memory Management System
**テスト担当**: 宏啓（プロジェクトオーナー）

---

## 1. テスト概要

### 1.1 目的

Memory Management Systemが仕様通りに実装され、3層AI構造（Yuno/Kana/Tsumu）の共鳴状態、意図履歴、選択肢を正しく永続化できることを確認する。

### 1.2 テスト環境要件

```bash
# Python環境
Python 3.11+
pip install pydantic pytest pytest-asyncio

# 依存パッケージ確認
pip list | grep -E "(pydantic|pytest)"
```

### 1.3 テスト実行方法

```bash
cd /path/to/resonant-engine

# 全テスト実行
python -m pytest tests/memory/ -v

# 特定テストのみ
python -m pytest tests/memory/test_models.py -v
python -m pytest tests/memory/test_service.py -v

# カバレッジ付き
python -m pytest tests/memory/ --cov=bridge/memory --cov-report=html
```

---

## 2. 自動テスト確認

### 2.1 モデルテスト（40ケース）

| テストID | テスト名 | 期待結果 | 確認欄 |
|----------|---------|----------|--------|
| M-01 | Session作成（デフォルト値） | UUID生成、status=active | ☐ |
| M-02 | Session作成（メタデータ付き） | メタデータ保持 | ☐ |
| M-03 | SessionStatusEnum | 4値: active, paused, completed, archived | ☐ |
| M-04 | SessionJSON シリアライズ | ISO形式の日時 | ☐ |
| M-05 | Intent作成 | status=pending, priority=0 | ☐ |
| M-06 | Intent階層構造 | parent_intent_id正常設定 | ☐ |
| M-07 | Intent優先度バリデーション（正常） | 0-10の範囲内成功 | ☐ |
| M-08 | Intent優先度バリデーション（異常） | 11以上でValidationError | ☐ |
| M-09 | IntentStatusEnum | 5値: pending, in_progress等 | ☐ |
| M-10 | IntentTypeEnum | 8値: feature_request, bug_fix等 | ☐ |
| M-11 | Resonance作成 | 強度・状態・エージェント設定 | ☐ |
| M-12 | Resonance強度バリデーション（正常） | 0.0-1.0範囲内成功 | ☐ |
| M-13 | Resonance強度バリデーション（異常） | 範囲外でValidationError | ☐ |
| M-14 | Resonanceエージェント正規化 | 大文字→小文字変換 | ☐ |
| M-15 | ResonanceStateEnum | 5値: aligned, conflicted等 | ☐ |
| M-16 | AgentContext作成 | version=1, context_data保持 | ☐ |
| M-17 | AgentContextバージョニング | superseded_by正常設定 | ☐ |
| M-18 | AgentTypeEnum | 3値: yuno, kana, tsumu | ☐ |
| M-19 | AgentContextバージョン検証 | version<1でValidationError | ☐ |
| M-20 | ChoicePoint作成（未決定） | selected_choice_id=NULL | ☐ |
| M-21 | ChoicePoint作成（決定済み） | 選択ID・理由・決定日時 | ☐ |
| M-22 | ChoicePoint最小選択肢 | 2未満でValidationError | ☐ |
| M-23 | ChoicePoint一意ID | 重複IDでValidationError | ☐ |
| M-24 | BreathingCycle作成 | phase設定、completed_at=NULL | ☐ |
| M-25 | BreathingCycleデータ付き | phase_data保持 | ☐ |
| M-26 | BreathingPhaseEnum | 6値: intake, resonance等 | ☐ |
| M-27 | BreathingCycle完了状態 | success設定 | ☐ |
| M-28 | Snapshot作成 | type, data設定 | ☐ |
| M-29 | Snapshotタグ付き | tags, description保持 | ☐ |
| M-30 | SnapshotTypeEnum | 5値: manual, milestone等 | ☐ |
| M-31 | SnapshotJSONシリアライズ | 全フィールド保持 | ☐ |
| M-32 | UUID一意性 | 全モデルで異なるUUID生成 | ☐ |
| M-33 | 日時タイムゾーン認識 | tzinfo非NULL | ☐ |
| M-34 | 日時シリアライズ | ISO形式文字列 | ☐ |

**実行結果**: ☐ PASS / ☐ FAIL

---

### 2.2 サービステスト（32ケース）

| テストID | テスト名 | 期待結果 | 確認欄 |
|----------|---------|----------|--------|
| S-01 | セッション開始 | UUID生成、status=active | ☐ |
| S-02 | セッション開始（メタデータ付き） | メタデータ保持 | ☐ |
| S-03 | セッション取得 | ID一致 | ☐ |
| S-04 | セッションハートビート | last_active更新 | ☐ |
| S-05 | セッションステータス更新 | 新status反映 | ☐ |
| S-06 | セッションサマリー取得 | 統計情報含む | ☐ |
| S-07 | Intent記録 | status=pending, 優先度設定 | ☐ |
| S-08 | Intent階層記録 | parent_intent_id設定 | ☐ |
| S-09 | Intent取得 | ID一致 | ☐ |
| S-10 | Intentステータス更新 | 新status反映 | ☐ |
| S-11 | Intent完了 | outcome設定、completed_at非NULL | ☐ |
| S-12 | Intent検索 | テキストマッチ | ☐ |
| S-13 | Intentリスト（ステータスフィルタ） | フィルタ正常動作 | ☐ |
| S-14 | Resonance記録 | state, intensity, agents設定 | ☐ |
| S-15 | Resonanceリスト | 全件取得 | ☐ |
| S-16 | Resonanceリスト（状態フィルタ） | state一致のみ | ☐ |
| S-17 | Resonance統計 | total, avg_intensity, distribution | ☐ |
| S-18 | AgentContext保存 | version=1設定 | ☐ |
| S-19 | AgentContextバージョニング | version増加、superseded_by設定 | ☐ |
| S-20 | AgentContext最新取得 | 最新version返却 | ☐ |
| S-21 | 全AgentContext取得 | 3層分取得 | ☐ |
| S-22 | ChoicePoint作成 | 未決定状態 | ☐ |
| S-23 | ChoicePoint決定 | 選択ID・理由・日時設定 | ☐ |
| S-24 | ChoicePoint未決定リスト | 未決定のみ | ☐ |
| S-25 | ChoicePoint無効選択エラー | ValueError発生 | ☐ |
| S-26 | BreathingCycle開始 | completed_at=NULL | ☐ |
| S-27 | BreathingCycle完了 | success設定、completed_at非NULL | ☐ |
| S-28 | 現在BreathingCycle取得 | 未完了cycle | ☐ |
| S-29 | BreathingCycleリスト | 全件取得 | ☐ |
| S-30 | Snapshot作成 | 全状態含む | ☐ |
| S-31 | Snapshotから復元 | snapshot_data取得 | ☐ |
| S-32 | セッション継続 | contexts, pending_choices, last_intent | ☐ |

**実行結果**: ☐ PASS / ☐ FAIL

---

## 3. 手動テスト

### 3.1 モジュールインポート確認

```python
# Python REPL で実行
python -c "
from bridge.memory import (
    Session, SessionStatus,
    Intent, IntentStatus, IntentType,
    Resonance, ResonanceState,
    AgentContext, AgentType,
    ChoicePoint, Choice,
    BreathingCycle, BreathingPhase,
    Snapshot, SnapshotType,
)
print('✅ 全モデルインポート成功')
"
```

**期待結果**: `✅ 全モデルインポート成功`
**確認欄**: ☐

---

### 3.2 サービス機能統合テスト

以下のPythonスクリプトを実行:

```python
# test_manual_integration.py
import asyncio
from bridge.memory.service import MemoryManagementService
from bridge.memory.in_memory_repositories import *
from bridge.memory.models import *

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

    print("=== Memory Management System 統合テスト ===\n")

    # 1. セッション開始
    print("1. セッション開始...")
    session = await service.start_session("hiroaki", {"client": "test"})
    print(f"   ✅ Session ID: {session.id}")
    print(f"   ✅ Status: {session.status}")

    # 2. Intent記録（呼吸フェーズ1: 吸う）
    print("\n2. Intent記録（呼吸フェーズ1: 吸う）...")
    intent = await service.record_intent(
        session.id,
        "Memory Management System実装",
        IntentType.FEATURE_REQUEST,
        priority=9,
    )
    print(f"   ✅ Intent ID: {intent.id}")
    print(f"   ✅ Priority: {intent.priority}")
    print(f"   ✅ Status: {intent.status}")

    # 3. Resonance記録（呼吸フェーズ2: 共鳴）
    print("\n3. Resonance記録（呼吸フェーズ2: 共鳴）...")
    resonance = await service.record_resonance(
        session.id,
        ResonanceState.ALIGNED,
        0.92,
        ["yuno", "kana", "tsumu"],
        intent_id=intent.id,
        pattern_type="full_layer_alignment",
    )
    print(f"   ✅ Resonance ID: {resonance.id}")
    print(f"   ✅ State: {resonance.state}")
    print(f"   ✅ Intensity: {resonance.intensity}")
    print(f"   ✅ Agents: {resonance.agents}")

    # 4. ChoicePoint作成（呼吸フェーズ3: 構造化）
    print("\n4. ChoicePoint作成（呼吸フェーズ3: 構造化）...")
    choice_point = await service.create_choice_point(
        session.id,
        intent.id,
        "PostgreSQL vs SQLite?",
        [
            Choice(id="pg", description="PostgreSQL", implications={"pros": ["JSONB", "scalability"]}),
            Choice(id="sqlite", description="SQLite", implications={"pros": ["simple", "lightweight"]}),
        ],
    )
    print(f"   ✅ ChoicePoint ID: {choice_point.id}")
    print(f"   ✅ Question: {choice_point.question}")
    print(f"   ✅ Choices: {len(choice_point.choices)}個")
    print(f"   ✅ Selected: {choice_point.selected_choice_id} (未決定)")

    # 5. Choice決定
    print("\n5. Choice決定...")
    decided = await service.decide_choice(
        choice_point.id,
        "pg",
        "Yuno評価A+。JSONB、並行性、将来性を考慮。"
    )
    print(f"   ✅ Selected Choice: {decided.selected_choice_id}")
    print(f"   ✅ Rationale: {decided.decision_rationale}")
    print(f"   ✅ Decided At: {decided.decided_at}")

    # 6. AgentContext保存（呼吸フェーズ4: 再内省）
    print("\n6. AgentContext保存（呼吸フェーズ4: 再内省）...")
    for agent_type in [AgentType.YUNO, AgentType.KANA, AgentType.TSUMU]:
        context = await service.save_agent_context(
            session.id,
            agent_type,
            {
                "focus": "Memory Management",
                "decisions": ["PostgreSQL選択"],
                "insights": [f"{agent_type.value}層からの洞察"],
            },
            intent_id=intent.id,
        )
        print(f"   ✅ {agent_type.value}: version {context.version}")

    # 7. BreathingCycle（呼吸フェーズ5: 実装）
    print("\n7. BreathingCycle記録（呼吸フェーズ5: 実装）...")
    cycle = await service.start_breathing_phase(
        session.id,
        BreathingPhase.IMPLEMENTATION,
        intent_id=intent.id,
        phase_data={"action": "schema_design"},
    )
    print(f"   ✅ Cycle ID: {cycle.id}")
    print(f"   ✅ Phase: {cycle.phase}")

    completed_cycle = await service.complete_breathing_phase(
        cycle.id,
        success=True,
        phase_data={"outcome": "8テーブル完成"},
    )
    print(f"   ✅ Completed: {completed_cycle.completed_at}")
    print(f"   ✅ Success: {completed_cycle.success}")

    # 8. Snapshot作成（時間軸保全）
    print("\n8. Snapshot作成（時間軸保全）...")
    snapshot = await service.create_snapshot(
        session.id,
        SnapshotType.MILESTONE,
        description="Memory Management System実装完了",
        tags=["memory", "milestone", "sprint"],
    )
    print(f"   ✅ Snapshot ID: {snapshot.id}")
    print(f"   ✅ Type: {snapshot.snapshot_type}")
    print(f"   ✅ Tags: {snapshot.tags}")
    print(f"   ✅ Data Keys: {list(snapshot.snapshot_data.keys())}")

    # 9. セッションサマリー
    print("\n9. セッションサマリー...")
    summary = await service.get_session_summary(session.id)
    print(f"   ✅ Total Intents: {summary['total_intents']}")
    print(f"   ✅ Completed Intents: {summary['completed_intents']}")
    print(f"   ✅ Resonance Events: {summary['resonance_events']}")
    print(f"   ✅ Choice Points: {summary['choice_points']}")
    print(f"   ✅ Breathing Cycles: {summary['breathing_cycles']}")
    print(f"   ✅ Avg Intensity: {summary['avg_intensity']:.2f}")

    # 10. セッション継続性テスト
    print("\n10. セッション継続性テスト...")
    await service.update_session_status(session.id, SessionStatus.PAUSED)
    continued = await service.continue_session(session.id)
    print(f"   ✅ Session Status: {continued['session'].status}")
    print(f"   ✅ Agent Contexts: {list(continued['agent_contexts'].keys())}")
    print(f"   ✅ Last Intent: {continued['last_intent'].intent_text}")
    print(f"   ✅ Pending Choices: {len(continued['pending_choices'])}")

    print("\n=== 全テスト完了 ✅ ===")

if __name__ == "__main__":
    asyncio.run(main())
```

**実行コマンド**:
```bash
python test_manual_integration.py
```

**期待結果**: 全ステップで `✅` が表示される
**確認欄**: ☐

---

### 3.3 API エンドポイント確認（オプション）

FastAPIサーバーを起動してSwagger UIで確認:

```bash
# サーバー起動（bridge/api/app.py にrouter組み込み必要）
uvicorn bridge.api.app:app --reload --port 8000

# Swagger UI確認
open http://localhost:8000/docs
```

**確認項目**:
- ☐ /api/memory/health が200を返す
- ☐ 全エンドポイントが表示される
- ☐ リクエスト/レスポンススキーマが正しい

---

## 4. 哲学準拠テスト

### 4.1 時間軸保全

| 確認項目 | 期待動作 | 確認欄 |
|----------|----------|--------|
| Intent完了後も履歴が残る | completed_atに日時設定、削除されない | ☐ |
| AgentContextバージョン保持 | 旧バージョンがsuperseded_by で参照可能 | ☐ |
| Snapshotで完全状態保存 | session, intents, resonances等全て含む | ☐ |

### 4.2 選択肢保持

| 確認項目 | 期待動作 | 確認欄 |
|----------|----------|--------|
| ChoicePoint未決定状態可能 | selected_choice_id=NULL が有効 | ☐ |
| 決定後も全選択肢保持 | choicesフィールドに元の選択肢全て残る | ☐ |
| 決定理由記録 | decision_rationaleに理由が保存される | ☐ |

### 4.3 呼吸サイクル対応

| フェーズ | 機能 | 確認欄 |
|----------|------|--------|
| 1. 吸う (Intake) | record_intent() | ☐ |
| 2. 共鳴 (Resonance) | record_resonance() | ☐ |
| 3. 構造化 (Structuring) | create_choice_point() | ☐ |
| 4. 再内省 (Re-reflection) | save_agent_context() | ☐ |
| 5. 実装 (Implementation) | create_snapshot() | ☐ |
| 6. 共鳴拡大 (Resonance Expansion) | continue_session() | ☐ |

---

## 5. パフォーマンス確認（オプション）

### 5.1 検索性能

```python
# 1000件Intentでの検索テスト
import time
async def perf_test():
    service = create_service()
    session = await service.start_session("perf_test")

    # 1000件作成
    for i in range(1000):
        await service.record_intent(
            session.id,
            f"Intent {i}: {'PostgreSQL' if i % 10 == 0 else 'Task'}",
            IntentType.EXPLORATION,
        )

    # 検索時間計測
    start = time.time()
    results = await service.search_intents(session.id, "PostgreSQL", limit=100)
    elapsed_ms = (time.time() - start) * 1000

    print(f"検索時間: {elapsed_ms:.2f}ms")
    print(f"結果件数: {len(results)}")
    # 期待: <100ms
```

**期待結果**: 100ms未満
**確認欄**: ☐

---

## 6. 受け入れ基準

### 6.1 必須基準（全て満たす必要あり）

- ☐ 自動テスト72件全てPASS
- ☐ 全モジュールインポート成功
- ☐ 統合テストスクリプト正常完了
- ☐ 呼吸サイクル6フェーズ全対応確認
- ☐ 時間軸保全（Snapshot機能）動作確認
- ☐ 選択肢保持（未決定状態）動作確認

### 6.2 推奨基準

- ☐ API Swagger UIで全エンドポイント確認
- ☐ パフォーマンステスト（検索<100ms）
- ☐ ドキュメント3種類の内容確認

---

## 7. 不具合報告フォーマット

問題が見つかった場合は以下の形式で報告:

```markdown
## 不具合報告

**テストID**: S-15
**テスト名**: Resonanceリスト
**期待結果**: 全件取得
**実際の結果**: [実際の動作]
**再現手順**:
1. ...
2. ...
3. ...

**エラーメッセージ**:
```
[エラー内容]
```

**環境情報**:
- Python: [version]
- OS: [OS name]
- Pydantic: [version]
```

---

## 8. テスト完了チェックリスト

- ☐ 自動テスト実行完了
- ☐ 手動テスト実行完了
- ☐ 哲学準拠確認完了
- ☐ 受け入れ基準全項目確認
- ☐ 不具合があれば報告済み

**テスト結果**: ☐ 合格 / ☐ 不合格（要修正）

**テスト実施者**: _________________
**実施日**: _________________
**署名**: _________________

---

## 付録: クイックスタートコマンド

```bash
# テスト環境準備
cd /path/to/resonant-engine
pip install pydantic pytest pytest-asyncio

# 自動テスト実行
python -m pytest tests/memory/ -v

# 統合テスト実行
python test_manual_integration.py

# カバレッジレポート
python -m pytest tests/memory/ --cov=bridge/memory --cov-report=html
open htmlcov/index.html
```
