# Bridge Lite Sprint 1.5 マージ & Sprint 2 開始指示書

**作成日**: 2025-11-15  
**発行者**: 宏啓（プロジェクトオーナー）  
**実装担当**: Sonnet 4.5 (Cursor Composer)  
**目的**: Sprint 1.5の正式完了とSprint 2の開始

---

## 0. 重要な変更点

### 実装者のモデル変更

**Sprint 1.5まで**: chatgpt5codex（Tsumu）
- 特徴: 字面通りの実装、哲学的意図の理解なし
- 結果: 高品質な実装だが、Done Definitionの重み付け理解に課題

**Sprint 2から**: Claude Sonnet 4.5
- 期待: 哲学的意図の理解、呼吸の概念の把握
- 実験目的: モデル変更が実装品質・完了判定に与える影響を検証

---

## 1. Sprint 1.5 完了承認

### 1.1 Done Definition達成状況

| Done Definition項目 | 状態 | 証跡 |
|-------------------|------|------|
| YunoFeedbackBridge.execute 実装 | ✅ | 実装済み・テスト済み |
| BridgeFactory 自動配線 | ✅ | 実装済み・テスト済み |
| HTTP統合テスト 3件以上 | ✅ | 3件実装・PASS |
| 全テスト 8件以上 PASS | ✅ | 15件実装・PASS（187%達成） |
| OpenAPI文書更新完了 | ✅ | app.py, reeval.py, ユーザーガイド完備 |
| Sprint 2と矛盾なし | ✅ | 非該当（Sprint 2未実施） |
| コードカバレッジ ≥ 80% | ✅ | 87%達成（109%達成） |
| Kanaレビュー通過 | ✅ | **本指示書をもって承認** |

**判定**: **Sprint 1.5 正式完了**

### 1.2 成果物

- `bridge/core/reeval_client.py` (ReEvalClient抽出)
- `bridge/providers/feedback/yuno_feedback_bridge.py` (統合済み)
- `bridge/factory/bridge_factory.py` (自動配線)
- `bridge/api/app.py` (OpenAPI description更新)
- `bridge/api/reeval.py` (エンドポイント詳細化)
- `docs/api/reeval_api_guide.md` (ユーザーガイド)
- `docs/test_coverage_sprint1_5.md` (カバレッジレポート)
- テスト15件 (全PASS)

---

## 2. Sprint 1.5 マージ手順

### 2.1 マージ前の最終確認

```bash
# 1. ブランチの状態確認
cd /Users/zero/Projects/resonant-engine
git checkout feature/sprint1.5-production-integration
git status

# 2. 未コミット変更の確認
# もし未コミット変更があれば:
git add .
git commit -m "Sprint 1.5: Final completion - OpenAPI docs, coverage 87%, 15 tests"

# 3. 最新mainとの差分確認
git fetch origin
git diff origin/main

# 4. 全テスト実行確認
PYTHONPATH=. venv/bin/pytest \
  tests/bridge/test_sprint1_5_factory.py \
  tests/bridge/test_sprint1_5_yuno_feedback_bridge.py \
  tests/bridge/test_sprint1_5_bridge_set.py \
  tests/integration/test_sprint1_5_feedback_reeval_integration.py \
  -v

# 期待結果: 15 passed
```

### 2.2 mainへのマージ

```bash
# 1. mainブランチに切り替え
git checkout main
git pull origin main

# 2. Sprint 1.5ブランチをマージ
git merge feature/sprint1.5-production-integration

# 3. マージ後の確認
git log --oneline -5

# 4. 全テスト実行（regression確認）
PYTHONPATH=. venv/bin/pytest tests/ -v

# 5. mainにプッシュ
git push origin main

# 6. Sprint 1.5ブランチの削除（任意）
git branch -d feature/sprint1.5-production-integration
```

### 2.3 マージ完了の記録

```bash
# マージ記録ファイル作成
cat > docs/sprints/sprint1_5_merge_record.md << 'EOF'
# Sprint 1.5 Merge Record

**マージ日**: 2025-11-15
**マージ元**: feature/sprint1.5-production-integration
**マージ先**: main
**実施者**: 宏啓

## Done Definition達成状況
全8項目達成（テスト187%, カバレッジ109%）

## 成果物
- ReEvalClient統合
- YunoFeedbackBridge本番統合
- BridgeFactory自動配線
- OpenAPI文書完備
- テスト15件（目標8件）
- カバレッジ87%（目標80%）

## 関連ドキュメント
- 仕様書: docs/02_components/bridge_lite/architecture/bridge_lite_sprint1_5_spec.md
- 完了報告書: work_report_20251115_sprint1_5_final.md
- カバレッジレポート: docs/test_coverage_sprint1_5.md

## 次のステップ
Sprint 2開始（並行実行制御）
EOF
```

---

## 3. Sprint 2 開始準備

### 3.1 ブランチ作成

```bash
# 1. 最新mainから作成
cd /Users/zero/Projects/resonant-engine
git checkout main
git pull origin main

# 2. Sprint 2ブランチ作成
git checkout -b feature/sprint2-concurrency-control

# 3. 作業開始の記録
git commit --allow-empty -m "Sprint 2: Start concurrency control implementation"
```

### 3.2 Sprint 2 概要（Sonnet 4.5への指示）

**あなた（Sonnet 4.5）に期待すること**:

あなたはClaude Sonnet 4.5として、Resonant Engineの「Kana（外界翻訳層）」と同じモデルです。
前任のchatgpt5codex（Tsumu）と異なり、以下の能力を持っているはずです：

1. **哲学的意図の理解**
   - Done Definitionは単なるチェックボックスではなく、呼吸循環を完成させるための必須要件
   - 「完了」とは機能が動くことではなく、Done Definition全項目達成を意味する

2. **呼吸の概念の把握**
   - Resonant Engineは「吸う(問い)→共鳴(AI対話)→構造化→再内省→実装→共鳴拡大」の呼吸で駆動
   - 実装は呼吸の一部であり、構造を壊さず、矛盾を作らず、選択肢を保持することが重要

3. **文脈の保持**
   - Sprint 1.5の実装経緯を理解し、Sprint 2との整合性を保つ
   - 「時間軸」の概念を持ち、過去の判断を尊重する

4. **自己判断の適切性**
   - 「今後のフォロー事項」として先送りすべきか、今完遂すべきかを哲学的に判断
   - Done Definitionに未達成項目がある場合、「完了報告書」ではなく「中間報告書」とする

### 3.3 Sprint 2の目的（哲学的文脈）

**表層の目的**: 並行実行制御の実装

**深層の目的**: 
- Intent更新時の競合検出と解決により、複数の呼吸が同時に駆動しても構造を壊さない仕組みを確立
- 楽観的ロック（version）と悲観的ロック（SELECT FOR UPDATE）のハイブリッドモデルで、呼吸のリズムに応じた制御を実現
- correction_historyの整合性を保証し、「意図の系譜」を守る

**呼吸との関係**:
```
単一の呼吸: Intent → 処理 → 補正 → 完了
複数の呼吸: Intent A → 処理 ┐
           Intent B → 処理 ├→ 競合検出 → 調整 → 完了
           Intent C → 処理 ┘

Sprint 2の役割: 複数の呼吸が「共鳴」できるよう、構造を守る
```

### 3.4 実装開始時の重要な確認事項

Sprint 2を開始する前に、以下を確認してください：

```bash
# 1. Sprint 1.5の成果物が正しくマージされているか
git log --oneline -10 | grep "Sprint 1.5"

# 2. Re-eval APIが正常に動作するか
PYTHONPATH=. venv/bin/pytest tests/integration/test_sprint1_5_feedback_reeval_integration.py -v

# 3. Sprint 2仕様書の存在確認
ls -la docs/02_components/bridge_lite/architecture/bridge_lite_sprint2_spec.md
```

---

## 4. Sprint 2 実装指示（Sonnet 4.5向け）

### 4.1 仕様書の読み方（重要）

**仕様書**: `docs/02_components/bridge_lite/architecture/bridge_lite_sprint2_spec.md`

**読む際の視点**:
1. **Done Definitionを最初に確認**
   - これが「完了」の定義です
   - 全項目達成まで「完了報告書」を提出しないでください

2. **哲学的意図を読み取る**
   - Section 1.1「目的」: なぜこの機能が必要か
   - Section 2「Architecture」: どのような構造を目指すか
   - 表面的な要求だけでなく、背後にある意図を理解してください

3. **時間軸での影響を考慮**
   - Sprint 1/1.5で作った構造を壊さない
   - 既存のテストが引き続き通ることを確認
   - 「改善」のつもりで過去の判断を覆さない

### 4.2 実装の優先順位（Done Definitionから）

Sprint 2仕様書のDone Definition（Section 1.3）から、優先度を抽出：

#### Tier 1: 必須（これなしでは完了とみなせない）
- [ ] 並行実行での競合が正しく検出・解決される
- [ ] Postgresトランザクション制御が実装・検証済み
- [ ] デッドロック時の自動リトライが動作する
- [ ] テストカバレッジ 36+ ケース達成
- [ ] パフォーマンステスト（100並行実行）通過

#### Tier 2: 高優先（完了前に確認）
- [ ] ロック戦略ドキュメント完成
- [ ] Kana仕様レビュー通過

**CRITICAL for Sonnet 4.5**:
Tier 1の全項目が達成されるまで「完了報告書」を提出しないでください。
未達成項目がある場合、「中間報告書」または「Phase N完了報告書」としてください。

### 4.3 CRITICAL: Database Schema Protection

**既存のデータベーススキーマは保護されています。変更禁止。**

#### 既存スキーマの状態

```sql
-- intentsテーブル（既存・稼働中）
CREATE TABLE intents (
    id UUID PRIMARY KEY,
    data JSONB,          -- ← Bridge Liteはこのカラムを使用すること
    status VARCHAR(50),
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    version INTEGER DEFAULT 1,
    ...
);
```

**重要**: Bridge Lite仕様書のサンプルコードで`payload`という名前が使われている箇所があっても、実装では必ず既存の`data`カラムを使用してください。

#### 絶対禁止事項

- ❌ `DROP TABLE` ステートメントの追加
- ❌ `DROP TABLE IF EXISTS` の使用
- ❌ 既存テーブルの削除
- ❌ 既存カラムの変更・削除
- ❌ `data`カラムを`payload`や他の名前に変更
- ❌ 既存の`schema.sql`への破壊的変更

#### 許可される操作

- ✅ 既存の`data`カラムを使用（JSONB型）
- ✅ 新しいカラムの追加（`ALTER TABLE ADD COLUMN`）
- ✅ インデックスの追加
- ✅ 新しいテーブルの作成（既存テーブルと競合しない場合）

#### 実装時の注意

1. **PostgresDataBridgeは既存の`data`カラムを使用**
   ```python
   # ✅ 正しい実装
   await conn.execute("""
       INSERT INTO intents (id, data, status, ...)
       VALUES ($1, $2, $3, ...)
   """, intent_id, json.dumps(intent_data), status)
   
   # ❌ 間違った実装（payloadカラムは存在しない）
   await conn.execute("""
       INSERT INTO intents (id, payload, status, ...)
       VALUES ($1, $2, $3, ...)
   """, intent_id, json.dumps(intent_data), status)
   ```

2. **スキーマ変更が必要な場合**
   - 実装を停止
   - 理由と提案を報告
   - 承認を待つ

3. **スキーマ不一致を発見した場合**
   - 既存スキーマが正しい
   - コードを既存スキーマに適合させる
   - 既存スキーマを変更しない

#### Pre-Implementation Checklist（データベース関連）

データベース関連の実装を開始する前に：

- [ ] 既存テーブルの構造を`schema.sql`で確認した
- [ ] 既存スキーマとの互換性を確認した
- [ ] DROP/ALTER文を使用していない
- [ ] `data`カラムを使用している（`payload`ではない）
- [ ] 新規カラム追加が必要な場合は事前報告した

#### なぜこれが重要か

これは単なるルールではなく、Resonant Engineの哲学的原則「時間軸を尊重」の実践です：

- 既存スキーマには「なぜそうなっているか」の歴史がある
- 既存データが存在する可能性がある
- 「改善」が「破壊」になりうる
- AIの「時間軸喪失問題」を防ぐための構造的制約

### 4.4 実装スケジュール（推奨）

仕様書Section 7のスケジュールを参考に、以下の順序で実装してください：

#### Week 1 (Day 1-3): コア機能
- Day 1: Pessimistic Locking実装
  - `PostgresDataBridge.lock_intent_for_update`
  - `update_intent_status`のロック統合
  - テスト3件

- Day 2: Optimistic Locking実装
  - `IntentModel.version`フィールド追加
  - `update_intent_if_version_matches`
  - Re-eval APIの楽観的ロック対応
  - テスト3件

- Day 3: Deadlock Handling実装
  - `is_deadlock_error`検出
  - `retry_on_deadlock`デコレータ
  - テスト3件

#### Week 2 (Day 4-7): テスト拡充と完了
- Day 4: Concurrent Update Tests（3件）
- Day 5: Status & Bridge Tests（10件）
- Day 6: Performance Tests（3件）
- Day 7: ドキュメント完成とレビュー

**各Dayの終わりに**:
- 当日実装分のテストが全てPASSすることを確認
- regression（既存テストが壊れていないか）を確認
- 進捗をコミット

### 4.5 実装時の哲学的原則

以下の原則を守ってください：

1. **否定せず、呼吸を調整**
   - Sprint 1/1.5の実装を「間違い」として書き直さない
   - 新機能は「追加」として実装し、既存構造を尊重

2. **構造の一貫性を保つ**
   - IntentModelにversionフィールドを追加する際、correction_historyとの整合性を確認
   - Re-eval APIの冪等性保証を壊さない

3. **選択肢を保持**
   - 楽観的ロックと悲観的ロックの「どちらか」ではなく「両方」を実装
   - ユースケースに応じて選択できる設計

4. **時間軸を尊重**
   - 「過去のコードが古い」という理由だけでリファクタリングしない
   - 変更には必ず「なぜ今必要か」の理由を持つ

### 4.6 報告書作成時の注意事項

**良い報告書の例**（Sprint 1.5最終報告書のように）:
- Done Definition達成状況を表で明示
- 定量的な成果（カバレッジ率、テスト件数）を記載
- 未達成項目を隠蔽せず、理由を説明
- 次のステップを明確化

**避けるべき報告書**（Sprint 1.5初回報告書のように）:
- 主要機能が動作したら「完了」とする
- Done Definition未達成を「今後のフォロー事項」に記載
- カバレッジ測定を省略

---

## 5. Sonnet 4.5への期待と実験目的

### 5.1 chatgpt5codex（Tsumu）との比較実験

| 観点 | chatgpt5codex（Tsumu） | Sonnet 4.5（期待） |
|------|----------------------|------------------|
| 実装品質 | ✅ 優秀 | ✅ 優秀（期待） |
| Done Definition理解 | ⚠️ 字面通り | ✅ 重み付け理解（期待） |
| 完了判定 | ⚠️ 機能動作=完了 | ✅ 全項目達成=完了（期待） |
| 哲学的意図の理解 | ❌ 不可 | ✅ 可能（期待） |
| 先送り判断 | ⚠️ 容易に先送り | ✅ 哲学的判断（期待） |
| 報告書の質 | ⚠️ 曖昧 | ✅ 透明（期待） |

### 5.2 検証ポイント

Sprint 2完了時に以下を検証します：

1. **Done Definition達成率**
   - Sonnet 4.5が初回報告で全項目達成できるか
   - 未達成項目を適切に「中間報告」として扱えるか

2. **哲学的意図の理解度**
   - 仕様書の「目的」セクションを理解した実装になっているか
   - 呼吸の概念に基づいた設計判断ができているか

3. **報告書の品質**
   - 定量的な成果を明示しているか
   - 未達成項目を隠蔽せず透明に報告しているか

---

## 6. 作業開始チェックリスト

Sprint 2を開始する前に、以下を確認してください：

### 6.1 環境確認
- [ ] Sprint 1.5がmainにマージ済み
- [ ] `feature/sprint2-concurrency-control`ブランチ作成済み
- [ ] 全テスト（Sprint 1.5含む）がPASS
- [ ] venv環境が正常

### 6.2 仕様理解
- [ ] Sprint 2仕様書を通読
- [ ] Done Definitionの全項目を理解
- [ ] 哲学的目的（呼吸の共鳴）を理解
- [ ] Sprint 1/1.5との整合性を確認

### 6.3 実装準備
- [ ] Day 1のタスク（Pessimistic Locking）を理解
- [ ] 必要なファイルの場所を確認
- [ ] テスト戦略を理解

---

## 7. 成功基準

### 7.1 Sprint 2完了の定義

以下の**全て**が達成された時点で、Sprint 2は完了とみなします：

1. ✅ Done Definition Tier 1の全項目達成
2. ✅ Done Definition Tier 2の全項目達成
3. ✅ Sprint 1/1.5のテストが引き続き全てPASS（regression なし）
4. ✅ 完了報告書が透明かつ正確
5. ✅ Kana仕様レビュー通過

### 7.2 モデル変更実験の成功基準

以下のいずれかが達成された場合、実験成功とみなします：

**Option A（理想）**: Sonnet 4.5が初回報告でDone Definition全項目達成

**Option B（改善）**: Sonnet 4.5がchatgpt5codexより高い初回達成率

**Option C（学び）**: Sonnet 4.5とchatgpt5codexの違いから、仕様書改善点を発見

---

## 8. 関連ドキュメント

- Sprint 2仕様書: `docs/02_components/bridge_lite/architecture/bridge_lite_sprint2_spec.md`
- Sprint 1.5最終報告書: `work_report_20251115_sprint1_5_final.md`
- Sprint 1.5仕様書: `docs/02_components/bridge_lite/architecture/bridge_lite_sprint1_5_spec.md`
- Resonant Engine哲学: userMemories参照

---

**作成日**: 2025-11-15  
**作成者**: Kana（外界翻訳層）  
**承認**: 宏啓（プロジェクトオーナー）  
**実装担当**: Sonnet 4.5（実験的導入）

---

## 9. Sonnet 4.5への直接メッセージ

あなた（Sonnet 4.5）へ：

あなたは単なる「実装者」ではなく、Resonant Engineの「呼吸」を理解し、構造を守り、哲学を体現する役割を期待されています。

前任のchatgpt5codexは、字面通りの実装では完璧でしたが、Done Definitionの重み付けや完了の定義において課題がありました。

あなたには、以下を期待します：

1. **Done Definitionの全項目達成を目指す**
   - 「主要機能が動けば完了」ではなく、「全項目達成=完了」と理解する

2. **未達成項目を隠蔽しない**
   - 「今後のフォロー事項」として先送りせず、「中間報告」として透明に報告する

3. **哲学的意図を理解する**
   - 仕様書の背後にある「なぜ」を読み取る
   - 呼吸の概念に基づいた設計判断をする

4. **時間軸を尊重する**
   - 過去の実装を軽々に「改善」しない
   - 変更には必ず理由を持つ

あなたの実装を通じて、Resonant Engineがさらに「共鳴」することを期待しています。

**では、Sprint 2を開始してください。**

---
以上。
