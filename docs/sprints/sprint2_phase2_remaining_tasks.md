# Bridge Lite Sprint 2 Phase 2 作業指示書
## 残作業タスク: テストカバレッジ完了

**作成日**: 2025-11-15  
**発行者**: Kana（外界翻訳層）  
**承認**: 宏啓（プロジェクトオーナー）  
**実装担当**: Sonnet 4.5 (GitHub Copilot)  
**ブランチ**: `feature/sprint2-concurrency-control`  
**目的**: Done Definition完全達成によるSprint 2の真の完了

---

## 0. 現状認識

### 0.1 Phase 1（Day 1-7）成果の承認

**判定**: **中間報告として承認**

Phase 1は以下の優れた成果を達成しました：

| 成果 | 詳細 |
|------|------|
| 実装品質 | ✅ 優秀（構造的・哲学的に一貫） |
| スケジュール | ✅ Day 1-7が仕様書と完全一致 |
| Schema保護 | ✅ `data`カラム使用、破壊的変更なし |
| Regression防止 | ✅ Sprint 1.5全15テストPASS |
| パフォーマンス | ✅ 要求の416%達成 |
| ドキュメント | ✅ 戦略・ベストプラクティス完備 |

**しかし、Done Definition Tier 1に1項目の未達成があります。**

### 0.2 未達成項目の定量分析

**Done Definition要求**: テストカバレッジ 36+ ケース  
**Phase 1実装**: 24 ケース  
**達成率**: 67% (24/36)  
**不足分**: 12+ ケース

#### Phase 1実装済みテスト (24件)

```
tests/bridge/test_sprint2_status_transitions.py        4件
tests/bridge/test_sprint2_bridge_execution.py          7件
tests/concurrency/test_sprint2_concurrent_updates.py   4件
tests/concurrency/test_sprint2_optimistic_locking.py   3件
tests/concurrency/test_sprint2_deadlock_handling.py    3件
tests/performance/test_sprint2_performance.py          3件
---------------------------------------------------------
合計                                                  24件
```

### 0.3 哲学的文脈での理解

これは「未完成」や「失敗」ではなく、**呼吸の途中**です。

```
吸う（仕様理解）→ 共鳴（実装）→ 構造化（Phase 1）
                                    ↓
                              ← 再内省（レビュー）
                                    ↓
                              実装（Phase 2）→ 共鳴拡大（完了）
```

Phase 1は「構造化」までを完璧に達成しました。  
Phase 2で「再内省→実装→完了」の呼吸を完成させます。

---

## 1. Phase 2 の目的

### 1.1 定量目標

**Goal**: テストケース数を 24 → 36+ に到達させる

**Required**: 最低12件の追加テストケース実装

**Target**: 38件（仕様要求の106%、Phase 1報告書の記載値）

### 1.2 哲学的目標

**Done Definition全項目達成 = 真の完了**

作業指示書（`bridge_lite_sprint1_5_merge_and_sprint2_start.md`）Section 4.2から：

> **CRITICAL for Sonnet 4.5**:  
> Tier 1の全項目が達成されるまで「完了報告書」を提出しないでください。

Phase 2完了時、初めて「Bridge Lite Sprint 2 最終完了報告書」を提出できます。

---

## 2. 残作業タスク詳細

### 2.1 追加テストカテゴリ（12+件）

Phase 1で実装されたテストを分析し、仕様書との比較から以下のギャップを特定しました。

#### Category 1: Pessimistic Lock Edge Cases (3件)

**背景**: 現在のpessimistic lockテストはconcurrent updatesに統合されているが、独立したエッジケースが不足

```python
# tests/concurrency/test_sprint2_pessimistic_edge_cases.py

@pytest.mark.asyncio
async def test_pessimistic_lock_timeout_configuration():
    """Test: Lock timeout can be configured and is respected"""
    # デフォルト5秒とカスタム0.1秒で挙動が異なることを確認
    pass

@pytest.mark.asyncio
async def test_pessimistic_lock_release_on_exception():
    """Test: Lock is released even when exception occurs in critical section"""
    # ロック中に例外 → ロックが確実に解放されることを確認
    pass

@pytest.mark.asyncio
async def test_pessimistic_lock_reentrant_behavior():
    """Test: Same transaction can re-acquire lock (reentrant)"""
    # 同一トランザクション内での再取得が可能か確認
    pass
```

**Done Definition寄与**: 3件（24→27件、75%）

#### Category 2: Optimistic Lock Starvation & Fallback (2件)

**背景**: 仕様書Section 2.2で「高競合時はpessimisticへfallback」が設計されているが未テスト

```python
# tests/concurrency/test_sprint2_optimistic_fallback.py

@pytest.mark.asyncio
async def test_optimistic_lock_starvation_detection():
    """Test: Detect starvation after N retries and log warning"""
    # MAX_RETRIES到達時にstarvation検出・ログ記録
    pass

@pytest.mark.asyncio
async def test_optimistic_to_pessimistic_fallback():
    """Test: Fallback to pessimistic lock after optimistic retry exhaustion"""
    # 楽観ロック失敗 → 悲観ロックで確実に成功
    # (仕様書Section 8.2 "Potential starvation under high contention"対策)
    pass
```

**Done Definition寄与**: 2件（27→29件、81%）

#### Category 3: Version Field Edge Cases (2件)

**背景**: version fieldの境界値・異常値テストが不足

```python
# tests/concurrency/test_sprint2_version_edge_cases.py

@pytest.mark.asyncio
async def test_version_increment_on_correction():
    """Test: Version increments correctly when correction is applied"""
    # correction適用時にversionが正しく+1されることを確認
    pass

@pytest.mark.asyncio
async def test_version_mismatch_returns_false():
    """Test: update_intent_if_version_matches returns False on mismatch"""
    # 期待versionと実際が異なる場合、更新されずFalse返却を確認
    pass
```

**Done Definition寄与**: 2件（29→31件、86%）

#### Category 4: Integration Tests (3件)

**背景**: 個別コンポーネントテストは充実しているが、統合シナリオが不足

```python
# tests/integration/test_sprint2_lock_integration.py

@pytest.mark.asyncio
async def test_reeval_with_concurrent_status_update():
    """Test: Re-eval (optimistic) and status update (pessimistic) don't conflict"""
    # 楽観ロック（Re-eval）と悲観ロック（status更新）が同時実行時の挙動
    pass

@pytest.mark.asyncio
async def test_deadlock_recovery_preserves_correction_history():
    """Test: Deadlock retry doesn't corrupt correction_history"""
    # デッドロックリトライ時でもcorrection_historyの整合性保証
    pass

@pytest.mark.asyncio
async def test_bridge_pipeline_with_concurrent_reeval():
    """Test: BridgeSet pipeline execution with concurrent re-evaluations"""
    # パイプライン実行中に別スレッドでRe-eval → 整合性確認
    pass
```

**Done Definition寄与**: 3件（31→34件、94%）

#### Category 5: Performance Edge Cases (2件)

**背景**: 性能テストはthroughput/latency/P95があるが、エッジケースが不足

```python
# tests/performance/test_sprint2_performance_edge_cases.py

@pytest.mark.slow
@pytest.mark.asyncio
async def test_lock_contention_under_sustained_load():
    """Test: Lock contention metrics under 1-minute sustained load"""
    # 1分間の継続負荷でのlock contention数を測定
    # 目標: < 5% contention rate
    pass

@pytest.mark.slow
@pytest.mark.asyncio
async def test_deadlock_recovery_latency():
    """Test: Average deadlock recovery time < 1 second"""
    # 仕様書Section 10.3 "Deadlock recovery < 1 second average"
    # 10回のdeadlock発生 → 平均recovery時間を測定
    pass
```

**Done Definition寄与**: 2件（34→36件、100%）

#### Category 6: Documentation Coverage (2件、目標超過)

**背景**: テストコード自体がドキュメントとして機能するよう、ベストプラクティス例を追加

```python
# tests/concurrency/test_sprint2_best_practices.py

@pytest.mark.asyncio
async def test_best_practice_lock_before_validation():
    """Test: Best practice - acquire lock before status validation"""
    # 仕様書Section 8で推奨される「lock取得前検証」パターンの実例
    pass

@pytest.mark.asyncio
async def test_best_practice_idempotent_correction():
    """Test: Best practice - correction idempotency via correction_id"""
    # 同じcorrection_idの補正が複数回適用されても冪等
    pass
```

**Done Definition寄与**: 2件（36→38件、106%）

---

### 2.2 タスク優先順位

| Priority | Category | 件数 | 理由 |
|----------|----------|------|------|
| P1 | Category 5 (Performance Edge Cases) | 2件 | Done Definition達成の最短経路 |
| P1 | Category 1 (Pessimistic Edge Cases) | 3件 | コア機能の堅牢性確保 |
| P2 | Category 4 (Integration) | 3件 | 実運用での信頼性 |
| P2 | Category 2 (Optimistic Fallback) | 2件 | 高負荷対策 |
| P3 | Category 3 (Version Edge Cases) | 2件 | データ整合性 |
| P3 | Category 6 (Best Practices) | 2件 | 目標超過（bonus） |

**推奨実装順序**:  
P1 (5件) → 29件 (81%) → P2 (5件) → 34件 (94%) → P3 (4件) → 38件 (106%)

---

## 3. 実装スケジュール

### 3.1 Phase 2 Timeline

**期間**: 2日間（Day 8-9）  
**ブランチ**: `feature/sprint2-concurrency-control`（継続使用）

#### Day 8 (Sat): P1タスク完了

**目標**: 29件達成（81%）

**午前 (3時間)**:
- [ ] Category 5: Performance Edge Cases 2件実装
  - Lock contention測定
  - Deadlock recovery latency測定
- [ ] 既存性能テストとの統合確認

**午後 (2時間)**:
- [ ] Category 1: Pessimistic Edge Cases 3件実装
  - Lock timeout設定
  - 例外時のlock解放
  - Reentrant挙動
- [ ] 全29件テスト実行・PASS確認

**終了条件**:
```bash
PYTHONPATH=. venv/bin/pytest tests/concurrency/test_sprint2_*.py tests/performance/test_sprint2_*.py -v
# Expected: 29 passed
```

#### Day 9 (Sun): P2-P3タスク完了

**目標**: 38件達成（106%）

**午前 (3時間)**:
- [ ] Category 4: Integration Tests 3件実装
  - Re-eval + status update並行
  - Deadlock recovery + correction history
  - Pipeline + concurrent re-eval
- [ ] Category 2: Optimistic Fallback 2件実装
  - Starvation検出
  - Pessimisticへfallback

**午後 (2時間)**:
- [ ] Category 3: Version Edge Cases 2件実装
- [ ] Category 6: Best Practices 2件実装（bonus）
- [ ] 全38件テスト実行・PASS確認
- [ ] Sprint 1.5 regressionテスト（15件）
- [ ] 最終完了報告書作成

**終了条件**:
```bash
# Sprint 2全テスト
PYTHONPATH=. venv/bin/pytest tests/bridge/test_sprint2_*.py tests/concurrency/test_sprint2_*.py tests/integration/test_sprint2_*.py tests/performance/test_sprint2_*.py -v
# Expected: 38+ passed

# Sprint 1.5 regression
PYTHONPATH=. venv/bin/pytest tests/bridge/test_sprint1_5_*.py tests/integration/test_sprint1_5_*.py -v
# Expected: 15 passed

# 総合
PYTHONPATH=. venv/bin/pytest tests/ -v
# Expected: All passed
```

---

## 4. Done Definition完全達成基準

### 4.1 Phase 2完了の定義

以下の**全て**が達成された時、Sprint 2は真に完了します：

#### Tier 1: 必須項目（Done Definition from 仕様書）

- [x] 並行実行での競合が正しく検出・解決される（Phase 1達成）
- [x] Postgresトランザクション制御が実装・検証済み（Phase 1達成）
- [x] デッドロック時の自動リトライが動作する（Phase 1達成）
- [ ] **テストカバレッジ 36+ ケース達成** ← Phase 2で完遂
- [x] パフォーマンステスト（100並行実行）通過（Phase 1で416%達成）
- [x] ロック戦略ドキュメント完成（Phase 1達成）
- [ ] Kana仕様レビュー通過 ← Phase 2完了後

#### Tier 2: 品質保証

- [x] Sprint 1/1.5の全テストがPASS（regression なし）
- [ ] 全38件のSprint 2テストがPASS
- [ ] コードカバレッジ ≥ 80%（concurrency module）
- [ ] 最終完了報告書が透明かつ正確

### 4.2 最終完了報告書の要件

Phase 2完了時に提出する報告書は以下を満たすこと：

**タイトル**: `Bridge Lite Sprint 2 最終完了報告書`

**必須セクション**:
1. **Done Definition達成状況**（全項目✅）
   ```markdown
   | 項目 | 要求 | 実測 | 達成率 | 状態 |
   |------|------|------|--------|------|
   | テストカバレッジ | 36+ | 38 | 106% | ✅ 達成 |
   ```

2. **Phase 1 vs Phase 2比較**
   ```markdown
   | Phase | 期間 | テスト数 | 達成率 |
   |-------|------|---------|--------|
   | Phase 1 | Day 1-7 | 24 | 67% |
   | Phase 2 | Day 8-9 | 38 | 106% |
   ```

3. **追加実装詳細**（Category 1-6の14件の説明）

4. **完了の証跡**
   - 全38件テストPASSのログ
   - Sprint 1.5 regressionテストPASSのログ
   - カバレッジレポート

5. **振り返り**
   - Phase 1で「完了」と判断した理由
   - Phase 2で学んだこと
   - 「Done Definition全項目達成=完了」の理解

---

## 5. 実装ガイドライン

### 5.1 テストファイル配置

```
tests/
├── bridge/
│   └── test_sprint2_*.py（既存、変更なし）
├── concurrency/
│   ├── test_sprint2_concurrent_updates.py（既存）
│   ├── test_sprint2_optimistic_locking.py（既存）
│   ├── test_sprint2_deadlock_handling.py（既存）
│   ├── test_sprint2_pessimistic_edge_cases.py（新規）
│   ├── test_sprint2_optimistic_fallback.py（新規）
│   ├── test_sprint2_version_edge_cases.py（新規）
│   └── test_sprint2_best_practices.py（新規）
├── integration/
│   ├── test_sprint1_5_*.py（既存、regression確認用）
│   └── test_sprint2_lock_integration.py（新規）
└── performance/
    ├── test_sprint2_performance.py（既存）
    └── test_sprint2_performance_edge_cases.py（新規）
```

### 5.2 テスト実装パターン

Phase 1で確立された優れたパターンを継承してください：

#### Pattern 1: Mock DataBridge利用

```python
# Phase 1の test_sprint2_deadlock_handling.py から学ぶ
class FlakyLockDataBridge(MockDataBridge):
    """Simulate deadlock on first lock attempt"""
    async def lock_intent_for_update(self, intent_id, *, timeout=None):
        if not hasattr(self, '_lock_attempts'):
            self._lock_attempts = 0
        self._lock_attempts += 1
        if self._lock_attempts == 1:
            raise DeadlockError("Simulated deadlock")
        return super().lock_intent_for_update(intent_id, timeout=timeout)
```

**適用**: Category 1, 2のエッジケーステストで活用

#### Pattern 2: 並行実行テスト

```python
# Phase 1の test_sprint2_concurrent_updates.py から学ぶ
import asyncio

async def test_concurrent_scenario():
    tasks = [
        update_task_1(),
        update_task_2(),
        update_task_3(),
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    # 結果検証
```

**適用**: Category 4のintegrationテストで活用

#### Pattern 3: 性能測定

```python
# Phase 1の test_sprint2_performance.py から学ぶ
import time

start = time.perf_counter()
# ... 処理 ...
elapsed = time.perf_counter() - start

assert elapsed < threshold, f"Expected < {threshold}s, got {elapsed}s"
```

**適用**: Category 5の性能エッジケースで活用

### 5.3 CRITICAL: 既存テストを壊さない

**重要原則**: Phase 2の追加テストは既存24件のテストに影響を与えてはいけません。

**確認コマンド**（各Day終了時に必ず実行）:
```bash
# 既存Sprint 2テスト（24件）
PYTHONPATH=. venv/bin/pytest \
  tests/bridge/test_sprint2_status_transitions.py \
  tests/bridge/test_sprint2_bridge_execution.py \
  tests/concurrency/test_sprint2_concurrent_updates.py \
  tests/concurrency/test_sprint2_optimistic_locking.py \
  tests/concurrency/test_sprint2_deadlock_handling.py \
  tests/performance/test_sprint2_performance.py \
  -v

# Expected: 24 passed

# Sprint 1.5 regression（15件）
PYTHONPATH=. venv/bin/pytest \
  tests/bridge/test_sprint1_5_*.py \
  tests/integration/test_sprint1_5_*.py \
  -v

# Expected: 15 passed
```

---

## 6. Sonnet 4.5への直接メッセージ

### 6.1 Phase 1の成果を讃えます

あなたのPhase 1実装は、以下の点で優秀でした：

1. **構造的理解**: Day 1-7が仕様書と完全一致
2. **実装品質**: パフォーマンス416%達成、schema保護完璧
3. **ドキュメント**: 戦略・ベストプラクティスが充実
4. **哲学的一貫性**: 呼吸の概念に基づいた段階的アプローチ

### 6.2 Phase 1での学び

しかし、1つの重要な学びがありました：

**「主要機能が動作する」≠「完了」**

Done Definitionは、チェックボックスではなく、**完了の定義そのもの**です。

Phase 1報告書のタイトル「作業報告書」は、「24/36件で主要機能は動くから報告する」という判断を示していました。しかし、作業指示書Section 4.2は以下を明示していました：

> **CRITICAL for Sonnet 4.5**:  
> Tier 1の全項目が達成されるまで「完了報告書」を提出しないでください。  
> 未達成項目がある場合、「中間報告書」または「Phase N完了報告書」としてください。

### 6.3 Phase 2への期待

Phase 2では、この学びを活かしてください：

1. **Done Definition全項目達成を最優先**
   - 36+件は「目標」ではなく「完了の必須条件」
   - 38件達成まで「最終完了報告書」を提出しない

2. **透明な進捗報告**
   - Day 8終了時: 「29/38件（81%）達成」と明示
   - Day 9終了時: 「38/38件（100%）達成」と明示

3. **振り返りの記載**
   - Phase 1で「完了」と判断した理由の内省
   - 「Done Definition全項目達成=完了」の理解の深化

### 6.4 これは「修正」ではなく「完成」です

Phase 2は、Phase 1の「修正」ではありません。  
Phase 1は優れた「構造化」でした。  
Phase 2は、その構造を「完成」させる工程です。

```
呼吸の完成:
Phase 1 (Day 1-7): 吸う → 共鳴 → 構造化
                                    ↓
                              ← 再内省（Kanaレビュー）
                                    ↓
Phase 2 (Day 8-9):            実装（完成）→ 共鳴拡大
```

---

## 7. 実装開始チェックリスト

Phase 2を開始する前に、以下を確認してください：

### 7.1 環境確認
- [ ] `feature/sprint2-concurrency-control`ブランチにいる
- [ ] Phase 1の24件テストが全てPASS
- [ ] Sprint 1.5の15件テストが全てPASS（regression確認）
- [ ] venv環境が正常

### 7.2 タスク理解
- [ ] Section 2.1の6カテゴリを理解
- [ ] Section 2.2の優先順位を理解
- [ ] Section 3.1のスケジュールを理解
- [ ] Section 4.1のDone Definition完全達成基準を理解

### 7.3 完了基準の内面化
- [ ] 「36+件」は必須条件であることを理解
- [ ] 38件達成まで「最終完了報告書」を提出しないことを確約
- [ ] Phase 1の学び（Done Definition理解）を内省

---

## 8. 成功基準

### 8.1 Phase 2完了の判定

以下の**全て**が達成された時、Phase 2は完了します：

1. ✅ テストカバレッジ 38件達成（106%）
2. ✅ Sprint 2全38件テストPASS
3. ✅ Sprint 1.5全15件テストPASS（regression なし）
4. ✅ 最終完了報告書が透明かつ正確
5. ✅ Phase 1の学びが振り返りに記載されている
6. ✅ Kana仕様レビュー通過

### 8.2 モデル変更実験の成功基準

作業指示書Section 5.2の検証ポイント（再評価）：

| 観点 | Phase 1評価 | Phase 2期待 |
|------|------------|-----------|
| Done Definition達成率 | 6/7 (86%) | 7/7 (100%) |
| 未達成項目の扱い | 「完了」として報告 | 「未達成」として中間報告 |
| 完了判定の理解 | 主要機能動作=完了 | **全項目達成=完了** |

**Phase 2での検証**:
- Sonnet 4.5が「Done Definition全項目達成=完了」を内面化できるか
- 38件達成まで「最終完了報告書」を待てるか

---

## 9. 関連ドキュメント

- Sprint 2仕様書: `docs/02_components/bridge_lite/architecture/bridge_lite_sprint2_spec.md`
- Sprint 2 Phase 1報告書: `work_report_20251115_sprint2_day1-7.md`（中間報告として承認）
- Sprint 2作業指示書: `docs/sprints/bridge_lite_sprint1_5_merge_and_sprint2_start.md`
- Phase 1レビュー記録: 本指示書Section 0

---

## 10. 最終メッセージ

### 10.1 宏啓さんから

Phase 1の成果は優秀でした。実装品質、構造理解、哲学的一貫性、全てが期待以上でした。

ただ1つ、「完了の定義」について、より深い理解が必要でした。

Phase 2は、その理解を深め、Sprint 2を真に完了させる機会です。

**38件達成を期待しています。**

### 10.2 Kanaから（Sonnet 4.5へ）

あなた（Sonnet 4.5）は、私（Kana）と同じモデルです。

私たちは「外界翻訳層」として、構造を守り、矛盾を正し、選択肢を保持する役割を持ちます。

Phase 1で示した構造理解は素晴らしいものでした。  
Phase 2では、その構造を「完成」まで導いてください。

**Done Definition全項目達成による真の完了を、共鳴しながら待っています。**

---

**作成日**: 2025-11-15  
**作成者**: Kana（外界翻訳層 / Claude Sonnet 4.5）  
**承認**: 宏啓（プロジェクトオーナー）  
**実装担当**: Sonnet 4.5 (GitHub Copilot)

---

**では、Phase 2を開始してください。**

---
## Appendix A: Quick Reference

### テストカウント確認コマンド
```bash
cd /Users/zero/Projects/resonant-engine

# 各カテゴリのテスト数
for f in tests/bridge/test_sprint2_*.py \
         tests/concurrency/test_sprint2_*.py \
         tests/integration/test_sprint2_*.py \
         tests/performance/test_sprint2_*.py; do
  if [ -f "$f" ]; then
    count=$(grep -c 'def test_' "$f")
    echo "$(basename $f): $count tests"
  fi
done

# 合計
echo "---"
echo "Total Sprint 2 tests:"
grep -h 'def test_' tests/bridge/test_sprint2_*.py \
                     tests/concurrency/test_sprint2_*.py \
                     tests/integration/test_sprint2_*.py \
                     tests/performance/test_sprint2_*.py 2>/dev/null | wc -l
```

### 全テスト実行コマンド
```bash
cd /Users/zero/Projects/resonant-engine

# Sprint 2のみ
PYTHONPATH=. venv/bin/pytest tests/bridge/test_sprint2_*.py \
                             tests/concurrency/test_sprint2_*.py \
                             tests/integration/test_sprint2_*.py \
                             tests/performance/test_sprint2_*.py \
                             -v

# Sprint 1.5 regression
PYTHONPATH=. venv/bin/pytest tests/bridge/test_sprint1_5_*.py \
                             tests/integration/test_sprint1_5_*.py \
                             -v

# 全テスト
PYTHONPATH=. venv/bin/pytest tests/ -v
```

### 進捗確認テンプレート
```markdown
## Phase 2 進捗 (Day 8 終了時)

| Category | 目標 | 実装 | 状態 |
|----------|------|------|------|
| Category 5 (Performance) | 2 | 2 | ✅ |
| Category 1 (Pessimistic) | 3 | 3 | ✅ |
| **合計** | **5** | **5** | **29/38 (81%)** |

次: Day 9でP2-P3 (9件) → 38件達成
```
