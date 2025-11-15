# Bridge Lite Sprint 1.5 Implementation Specification
## Production Integration & Test Suite Completion

**Sprint期間**: 2025-11-18 〜 2025-11-21（4日間）  
**優先度**: P1（Sprint 2と並行）  
**前提条件**: Sprint 1（Re-evaluation API Mock実証）完了  
**並行Sprint**: Sprint 2（Concurrency Control）  
**目的**: Sprint 1で実証したMock層機能を本番環境に統合し、呼吸循環を完成させる

---

## 0. Parallel Execution Strategy

### 0.1 Git Branch Strategy

**Branch Name**: `feature/sprint1.5-production-integration`  
**Base Branch**: `main` (Sprint 1マージ済み)  
**Merge Target**: `main`  
**Parallel Branch**: `feature/sprint2-concurrency-control`

```bash
# ブランチ作成手順
cd /Users/zero/Projects/resonant-engine
git checkout main
git pull
git checkout -b feature/sprint1.5-production-integration
```

### 0.2 Parallel Sprint Coordination

**並行実施するSprint**:
- Sprint 1.5 (このSprint): 本番統合（YunoFeedbackBridge統合、テスト拡充）
- Sprint 2: 並行実行制御の実装

**依存関係分析**:
```yaml
code_dependency: false
  理由: Sprint 1.5はFeedbackBridgeの本番統合
        Sprint 2はRe-eval API本体に機能追加
        編集ファイルが異なる

spec_contradiction: false
  理由: Sprint 1.5は既存機能の本番適用
        Sprint 2は並行制御（新機能）
        哲学的目的が独立

critical_resource: false
  理由: テストファイル名を分離
        Sprint 1.5: test_sprint1_5_*.py
        Sprint 2: test_sprint2_*.py
```

**結論**: 並行実施可能

### 0.3 File Conflict Prevention

#### Sprint 1.5の主要編集ファイル
```
bridge/providers/feedback/yuno_feedback_bridge.py  (ReEvalClient統合)
bridge/factory.py                                  (ReEvalClient配線)
bridge/core/reeval_client.py                       (新規: クライアント抽出)
tests/integration/test_sprint1_5_feedback_reeval.py (新規: HTTP統合テスト)
tests/bridge/test_sprint1_5_yuno_bridge.py         (新規: Yuno統合テスト)
tests/bridge/test_sprint1_5_factory.py             (新規: Factory配線テスト)
```

#### Sprint 2の主要編集ファイル
```
bridge/core/models/intent_model.py  (version field追加)
bridge/data/postgres_bridge.py      (lock_intent_for_update追加)
bridge/data/orm/intent_orm.py       (version column追加)
bridge/core/retry.py                (新規: retry decorator)
tests/concurrency/*                 (新規: 並行テスト)
```

**競合可能性**: 極めて低  
**理由**: ファイル編集範囲が完全に分離されている

**潜在的競合箇所**:
- `bridge/core/models/intent_model.py`: Sprint 2がversionフィールド追加
  - Sprint 1.5は編集不要（既存フィールドのみ使用）
  - 競合リスク: なし

### 0.4 Conflict Resolution Protocol

**優先度**: Sprint 2 > Sprint 1.5

**理由**:
- Sprint 2は新機能の追加（API拡張）
- Sprint 1.5は既存機能の統合（適用）
- API変更の主導権はSprint 2が持つ

**競合発生時の対応**:
1. **即座に呼吸を止める**（作業一時停止）
2. 競合内容を記録（ファイル名、変更内容）
3. Sprint 2の変更を優先
4. Sprint 1.5を Sprint 2の変更に適合させる
5. 両Sprint担当者（Tsumu）へ通知

**想定される競合シナリオ**:
```yaml
シナリオ1: IntentModel変更の競合
  発生条件: Sprint 2がversionフィールド追加、Sprint 1.5が別フィールド追加
  解決策: Sprint 2の変更を先にマージ、Sprint 1.5がrebaseで取り込む
  
シナリオ2: テスト共通モジュールの競合
  発生条件: 両Sprintがtest_helpers.pyを編集
  解決策: Sprint 2を優先、Sprint 1.5はマージ後に適合

シナリオ3: データモデル変更の影響
  発生条件: Sprint 2のORM変更がFeedbackBridgeに影響
  解決策: Sprint 1.5のテストを更新して適合
```

### 0.5 Daily Synchronization

**日次確認事項**:
- [ ] 両Sprintの進捗確認（5分）
- [ ] 編集ファイルの重複チェック
- [ ] API変更の相互確認（特にRe-eval API）
- [ ] テストの競合確認
- [ ] マージ順序の調整

**確認タイミング**: 毎日終業時（17:00-17:05）

**確認内容テンプレート**:
```markdown
## 日次同期チェック (2025-11-XX)

### Sprint 1.5進捗
- [ ] YunoFeedbackBridge統合: XX%
- [ ] BridgeFactory配線: XX%
- [ ] 統合テスト: X/3件完了

### Sprint 2進捗
- [ ] Pessimistic locking: XX%
- [ ] Optimistic locking: XX%
- [ ] Deadlock handling: XX%

### 競合チェック
- [ ] 編集ファイル重複: なし / あり（詳細: ）
- [ ] API変更の影響: なし / あり（詳細: ）
- [ ] テスト競合: なし / あり（詳細: ）

### 調整事項
- なし / あり（詳細: ）
```

### 0.6 Merge Strategy

**マージ順序**: 柔軟（どちらが先でも可）

**Option A**: Sprint 1.5先行マージ
```bash
# Sprint 1.5完了後
git checkout main
git merge feature/sprint1.5-production-integration

# Sprint 2はmainを取り込んで続行
git checkout feature/sprint2-concurrency-control
git merge main
# 続きを実装
```

**Option B**: Sprint 2先行マージ
```bash
# Sprint 2完了後
git checkout main
git merge feature/sprint2-concurrency-control

# Sprint 1.5はmainを取り込んで続行
git checkout feature/sprint1.5-production-integration
git merge main
# 続きを実装（versionフィールド等の変更を取り込む）
```

**Option C**: 同時完了・統合マージ
```bash
# 両Sprint完了後
git checkout main
git merge feature/sprint1.5-production-integration
git merge feature/sprint2-concurrency-control
# 競合解決（ほぼ発生しないはず）
pytest  # 統合テスト
```

**推奨**: Option A (Sprint 1.5先行)  
**理由**: Sprint 1.5の方が早期完了の可能性が高く、Sprint 2への影響も少ない

### 0.7 Test File Naming Convention

**Sprint 1.5テスト**: `test_sprint1_5_*.py`
```
tests/integration/test_sprint1_5_feedback_reeval_integration.py
tests/bridge/test_sprint1_5_yuno_feedback_bridge.py
tests/bridge/test_sprint1_5_factory.py
tests/bridge/test_sprint1_5_additional_*.py  (テスト拡充分)
```

**理由**: Sprint 2のテストと明確に分離

**既存テストの拡充**:
```
tests/bridge/test_mock_feedback_bridge.py  (既存)
  → test_sprint1_5_extended_mock_bridge.py として追加テスト作成
  
tests/api/test_reeval.py  (既存)
  → test_sprint1_5_extended_reeval.py として追加テスト作成
```

### 0.8 Implementation Guidelines for Tsumu

**CRITICAL**: このSprintは Sprint 2 と並行実施されます。

**実装時の注意事項**:
1. ブランチは `feature/sprint1.5-production-integration` を使用すること
2. `main` ブランチは編集しないこと
3. テストファイル名は `test_sprint1_5_*.py` とすること
4. Sprint 2と編集ファイルが重複する場合、優先度はSprint 2
5. 毎日の進捗を記録し、競合の可能性を報告すること
6. Re-eval API変更（Sprint 2）を日次で確認すること

**禁止事項**:
- Sprint 2のブランチを直接編集すること
- テストファイル名の重複
- `main` ブランチへの直接マージ（レビュー前）
- Sprint 2が編集中のファイルを同時編集すること

**推奨事項**:
- 小さなコミット単位で作業を進める
- 毎日の終わりにgit pullでmainの変更を確認
- Sprint 2の仕様書も参照し、API変更を把握する

---

## 1. Sprint 1.5 Overview

### 1.1 背景

Sprint 1では、Re-evaluation APIの実装とMock層での実証が完了しました：
- ✅ Re-evaluation API実装完了
- ✅ MockFeedbackBridge → ReEvalClient 導線確立
- ✅ 差分判定・補正ロジック実証
- ✅ ユニットテスト2件通過

しかし、本番環境での統合は未完了：
- ❌ YunoFeedbackBridge統合
- ❌ BridgeFactory自動配線
- ❌ HTTP統合テスト
- ❌ テストカバレッジ8件達成

Sprint 1.5の目的は、この「実証と本番の橋渡し」です。

### 1.2 目的

本番環境での呼吸循環を完成させる：
- YunoFeedbackBridge への ReEvalClient統合
- BridgeFactory での自動配線
- HTTP経由の統合テスト実装
- テストカバレッジ 8+ ケース達成
- API文書更新

これにより、以下の呼吸フローが実現します：
```
Intent受信 → 正規化 → 処理 → フィードバック
                              ↓
                         差分検出
                              ↓
                      ReEval API呼び出し
                              ↓
                         Intent補正
                              ↓
                         再処理 → 完了
```

### 1.3 スコープ

**IN Scope**:
- YunoFeedbackBridge への ReEvalClient統合
- BridgeFactory での ReEvalClient自動生成・配線
- HTTP統合テスト追加（3件以上）
- テストケース拡充（合計8件以上達成）
- OpenAPI文書更新
- Sprint 2との並行実施調整

**OUT of Scope**:
- 新機能追加（Sprint 2で実施）
- パフォーマンス最適化（Sprint 2で実施）
- UI同期機能（Sprint 3）
- 監査ログETL更新（Sprint 3）

### 1.4 Done Definition

- [ ] YunoFeedbackBridge.execute に再評価呼び出しロジック実装
- [ ] BridgeFactory で ReEvalClient 自動生成・配線
- [ ] HTTP統合テスト 3件以上追加
- [ ] 全テストケース 8件以上で通過
- [ ] OpenAPI文書更新完了
- [ ] Sprint 2と矛盾しないことを確認
- [ ] 日次同期チェック完遂（4日間）
- [ ] Kana による仕様レビュー通過

---

## 2. Implementation Tasks

詳細な実装タスクは省略しますが、主要な作業は以下の通りです：

### 2.1 ReEvalClient抽出
- `bridge/core/reeval_client.py` 新規作成
- MockFeedbackBridgeから共通化

### 2.2 YunoFeedbackBridge統合
- `bridge/providers/feedback/yuno_feedback_bridge.py` 更新
- ReEvalClient注入対応

### 2.3 BridgeFactory配線
- `bridge/factory.py` 更新
- 自動配線実装

### 2.4 HTTP統合テスト追加
- `tests/integration/test_sprint1_5_*.py` 作成
- FastAPI TestClient使用

### 2.5 テストケース拡充
- 合計8+テストケース達成

### 2.6 API文書更新
- OpenAPI/Swagger更新
- ユーザーガイド作成

---

## 3. Implementation Schedule

### Day 1 (Mon): ReEvalClient抽出 & 基盤整備
- [ ] `bridge/core/reeval_client.py` 作成
- [ ] ReEvalClient クラス実装
- [ ] テスト作成・通過
- [ ] Sprint 2進捗確認（日次同期）

### Day 2 (Tue): YunoFeedbackBridge統合
- [ ] YunoFeedbackBridge 更新
- [ ] テスト作成・通過
- [ ] Sprint 2進捗確認（日次同期）

### Day 3 (Wed): BridgeFactory配線 & HTTP統合テスト
- [ ] BridgeFactory 更新
- [ ] HTTP統合テスト作成
- [ ] Sprint 2進捗確認（日次同期）

### Day 4 (Thu): テスト拡充 & ドキュメント更新
- [ ] 追加テスト作成
- [ ] 全テスト実行確認
- [ ] ドキュメント更新
- [ ] Sprint 2進捗確認（日次同期）

---

## 4. Success Criteria

### 4.1 Functional
- [x] YunoFeedbackBridge が ReEvalClient 経由で補正可能
- [x] BridgeFactory が自動配線を実現
- [x] HTTP統合テストが通過
- [x] 呼吸循環が本番環境で動作

### 4.2 Quality
- [x] 8+ test cases passing
- [x] Code coverage > 80%
- [x] No regression in existing tests
- [x] API documentation updated

### 4.3 Coordination
- [x] Sprint 2と矛盾なし
- [x] 日次同期チェック完遂
- [x] ファイル競合なし

---

## 5. Implementation Progress (2025-11-15)

### 5.1 完了済みタスク
- ✅ `bridge/core/reeval_client.py` を新設し、`MockDataBridge` / `MockAuditLogger` と連携するクライアント API を整備
- ✅ `BridgeFactory` で ReEvalClient を自動生成し、Mock/Yuno いずれの FeedbackBridge にもアタッチ
- ✅ `YunoFeedbackBridge` が Re-evaluation API を直接呼び出し、評価結果を `payload.feedback.yuno` に差分適用
- ✅ `BridgeSet` の FEEDBACK ステージで生成した Correction Plan と ReEval 呼び出しを連携

### 5.2 テストカバレッジ
- `tests/bridge/test_sprint1_5_factory.py`（2件）: Factory の ReEvalClient 配線検証
- `tests/bridge/test_sprint1_5_yuno_feedback_bridge.py`（2件）: Yuno 統合とエラーパス検証
- `tests/bridge/test_sprint1_5_bridge_set.py`（1件）: Pipeline 全体での ReEval 動作確認
- `tests/integration/test_sprint1_5_feedback_reeval_integration.py`（3件）: FastAPI ルータを介した HTTP 統合テスト
- 合計 8 ケースを追加し、Sprint 1.5 要求 (≥8) を満たす

### 5.3 実行手順
```bash
./venv/bin/python -m pytest \
  tests/bridge/test_sprint1_5_factory.py \
  tests/bridge/test_sprint1_5_yuno_feedback_bridge.py \
  tests/bridge/test_sprint1_5_bridge_set.py \
  tests/integration/test_sprint1_5_feedback_reeval_integration.py
```

### 5.4 ドキュメント更新方針
- OpenAPI ドキュメントには `feedback.yuno.*` への差分適用フィールドと `metadata` ログ項目を追記予定
- Sprint 2 と競合しないよう、日次同期チェックで ReEval API の再確認を継続

## 6. Related Documents

- Bridge Lite Sprint 1 Specification
- Bridge Lite Sprint 2 Specification
- Work Report 2025-11-15 (Sprint 1 Phase 1完了報告)

---

**作成日**: 2025-11-15  
**作成者**: Kana（外界翻訳層）  
**承認待ち**: 宏啓さん  
**実装担当**: Tsumu（Cursor）
