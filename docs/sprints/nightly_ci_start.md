# Nightly CI 実装開始指示書
## Sprint 3完了後の継続的性能監視実装

**作成日**: 2025-11-16  
**発行者**: Kana（外界翻訳層 / Claude Sonnet 4.5）  
**承認待ち**: 宏啓（プロジェクトオーナー）  
**実装担当**: Sonnet 4.5 または Tsumu（Cursor）  
**目的**: Sprint 2性能ベースラインの継続的監視システム構築

---

## 0. 重要な前提条件

### Sprint 3の完了状態

**このタスクを開始する前に、Sprint 3が完全に完了している必要があります:**

- [ ] Sprint 3 Done Definition全項目達成
- [ ] リアルタイムUI同期実装完了
- [ ] テストカバレッジ 50+ ケース達成
- [ ] WebSocket/SSE負荷テスト通過
- [ ] 最終完了報告書作成済み
- [ ] Kana仕様レビュー通過

**Sprint 3未完了の場合:**
このタスクは実施せず、Sprint 3の完了を優先してください。

---

## 1. Nightly CI 実装承認

### 1.1 実装背景

Sprint 2で達成した性能ベースラインを保護し、将来的な劣化を早期検知するため、継続的な性能監視システムを構築します。

**Sprint 2 達成メトリクス**:
- Throughput: 416 updates/sec（目標100の416%）
- P95 Latency: 0.3 ms（目標50msを大幅に上回る）
- Deadlock Recovery: 0.8 sec（目標1秒以内）
- テストカバレッジ: 38件（106%達成）

**課題認識**:
- Sprint 3以降の機能追加が性能に影響する可能性
- 手動実行では継続的監視が困難
- 性能劣化を早期に検知する仕組みがない

### 1.2 実装スコープ

**実装するもの**:
- GitHub Actions Nightly ワークフロー
- 性能メトリクス抽出スクリプト
- 性能劣化検知スクリプト
- ベースライン設定ファイル
- Slack通知統合
- CI動作テスト（5件）
- 運用ドキュメント（3種類）

**実装しないもの**:
- フロントエンドダッシュボード（将来拡張）
- 性能テスト以外のCI統合（別途計画）
- マルチ環境テスト（将来拡張）

---

## 2. 実装手順

### 2.1 事前準備チェックリスト

実装を開始する前に、以下を確認してください：

#### 環境確認
- [ ] Sprint 3が main にマージ済み
- [ ] Sprint 2性能テスト（5件）が正常動作
- [ ] GitHub Actions が利用可能
- [ ] Slack Webhook URLが取得可能

#### 仕様理解
- [ ] 仕様書 `nightly_ci_spec.md` を通読
- [ ] Done Definitionの全項目を理解
- [ ] Sprint 2性能ベースラインを理解
- [ ] 3日間のスケジュールを理解

#### ツール準備
- [ ] Python 3.11+ 環境確認
- [ ] pytest, pytest-asyncio インストール確認
- [ ] GitHub CLI インストール（任意）

---

## 3. 実装スケジュール（3日間）

### Day 1 (6時間): Phase 1 - 基本CI構築

#### 午前 (3時間): ワークフロー作成

**タスク**:
1. `.github/workflows/` ディレクトリ作成
   ```bash
   mkdir -p /Users/zero/Projects/resonant-engine/.github/workflows
   ```

2. `nightly-performance.yml` 作成
   - 仕様書 Section 2.1 のYAMLをコピー
   - cronスケジュール設定: `0 18 * * *` (JST 3:00)
   - PostgreSQL 15サービス設定
   - Sprint 2性能テスト実行ステップ

3. GitHub Secrets設定
   ```bash
   # GitHub Settings → Secrets → Actions
   # SLACK_WEBHOOK_URL を追加
   ```

**検証**:
```bash
# 手動実行テスト
# GitHub Actions画面から "Run workflow" をクリック
# または GitHub CLI で:
gh workflow run nightly-performance.yml
```

**完了基準**:
- [ ] ワークフローファイルが作成済み
- [ ] 手動実行で成功
- [ ] Sprint 2性能テスト5件がCI環境でPASS
- [ ] JUnit XML出力が正常（`performance-results.xml`）

#### 午後 (3時間): トラブルシューティング & ドキュメント

**タスク**:
1. CI環境での問題解決
   - PostgreSQL接続エラー対応
   - タイムアウト設定調整
   - 依存関係の問題解決

2. 初版ドキュメント作成
   ```bash
   mkdir -p /Users/zero/Projects/resonant-engine/docs/operations
   ```
   - `nightly_ci_setup_guide.md` (基本版)

**検証**:
```bash
# 連続2回実行して安定性確認
gh workflow run nightly-performance.yml
# 10分待機
gh workflow run nightly-performance.yml
```

**完了基準**:
- [ ] 連続実行で安定動作
- [ ] 実行時間 < 15分
- [ ] セットアップガイド初版完成

---

### Day 2 (6時間): Phase 2-3 - メトリクス & 劣化検知

#### 午前 (3時間): スクリプト実装

**タスク1**: メトリクス抽出スクリプト
```bash
mkdir -p /Users/zero/Projects/resonant-engine/scripts
```

1. `scripts/extract_performance_metrics.py` 作成
   - 仕様書 Section 2.2 のコードをベースに実装
   - JUnit XMLパース処理
   - メトリクス抽出ロジック
   - JSON出力

2. ローカルテスト
   ```bash
   cd /Users/zero/Projects/resonant-engine
   
   # Sprint 2性能テスト実行してJUnit XML生成
   PYTHONPATH=. pytest tests/performance/test_sprint2_*.py \
     -m slow \
     --junitxml=test-results.xml
   
   # メトリクス抽出テスト
   python scripts/extract_performance_metrics.py \
     test-results.xml \
     test-metrics.json
   
   # 結果確認
   cat test-metrics.json
   ```

**タスク2**: 劣化検知スクリプト
```bash
mkdir -p /Users/zero/Projects/resonant-engine/config
```

1. `config/performance_baselines.json` 作成
   - 仕様書 Section 2.4 のJSONをコピー
   - Sprint 2ベースライン設定

2. `scripts/check_performance_regression.py` 作成
   - 仕様書 Section 2.3 のコードをベースに実装
   - ベースライン比較ロジック
   - 劣化検知ロジック
   - 警告メッセージ生成

3. ローカルテスト
   ```bash
   # 正常パターン（劣化なし）
   python scripts/check_performance_regression.py
   # 期待: exit 0, "✅ No performance regression detected"
   
   # 劣化パターン（テスト用に一時的にメトリクスを編集）
   # performance-metrics.json の throughput を 70 に変更
   python scripts/check_performance_regression.py
   # 期待: exit 1, "⚠️ REGRESSION: Throughput"
   ```

**完了基準**:
- [ ] メトリクス抽出スクリプトが正常動作
- [ ] 劣化検知スクリプトが正常動作
- [ ] ローカルテストで両パターン確認

#### 午後 (3時間): CI統合 & Slack通知

**タスク1**: ワークフローにスクリプト統合

`nightly-performance.yml` に以下を追加:
```yaml
- name: Extract performance metrics
  if: always()
  run: |
    python scripts/extract_performance_metrics.py \
      performance-results.xml \
      performance-metrics.json

- name: Check for performance regression
  if: always()
  run: |
    python scripts/check_performance_regression.py
  continue-on-error: true
  id: regression_check
```

**タスク2**: Slack通知設定

1. テスト用Webhookで通知テスト
   ```bash
   # 仕様書 Section 2.1 のSlack通知部分を確認
   ```

2. 通知パターンテスト
   - テスト失敗時の通知
   - 劣化検出時の通知（メトリクス詳細付き）

**検証**:
```bash
# 手動実行で全ステップ確認
gh workflow run nightly-performance.yml

# GitHub Actions画面で以下を確認:
# 1. Sprint 2性能テスト実行
# 2. メトリクス抽出
# 3. 劣化検知
# 4. Artifacts アップロード
# 5. Slack通知（該当時）
```

**完了基準**:
- [ ] 全ステップが正常動作
- [ ] Artifactsが正常アップロード
- [ ] Slack通知が正常送信（テスト確認）

---

### Day 3 (4時間): テスト & ドキュメント完成

#### 午前 (2時間): CI動作テスト実装

**タスク**: テストコード作成
```bash
mkdir -p /Users/zero/Projects/resonant-engine/tests/ci
```

1. `tests/ci/test_nightly_workflow.py` 作成
   - 仕様書 Section 3.1 のテストをベースに実装
   - 5件のテストケース:
     - `test_extract_metrics_script_exists`
     - `test_regression_check_script_exists`
     - `test_baseline_config_exists`
     - `test_baseline_config_structure`
     - `test_extract_metrics_script_runs`

2. テスト実行
   ```bash
   cd /Users/zero/Projects/resonant-engine
   PYTHONPATH=. pytest tests/ci/test_nightly_workflow.py -v
   
   # 期待結果: 5 passed
   ```

**完了基準**:
- [ ] 5件のテストが全てPASS
- [ ] スクリプトの存在確認
- [ ] 設定ファイルの構造検証

#### 午後 (2時間): ドキュメント完成 & 試験運用開始

**タスク1**: ドキュメント作成

1. `docs/operations/nightly_ci_setup_guide.md`
   - GitHub Actions有効化手順
   - Slack Webhook設定手順
   - 初回実行手順
   - トラブルシューティング

2. `docs/performance/baseline_management.md`
   - ベースライン更新タイミング
   - 更新手順
   - 意図的な性能変更時の対応

3. `docs/operations/nightly_ci_operations.md`
   - 日次確認事項
   - アラート対応フロー
   - 性能劣化時の調査手順

**タスク2**: 試験運用開始

1. cronスケジュール有効化確認
2. 翌日のCI実行結果を確認
3. 1週間の安定動作を監視

**完了基準**:
- [ ] ドキュメント3種類完成
- [ ] 手動実行で最終動作確認
- [ ] cronスケジュール設定確認

---

## 4. Done Definition完全達成基準

### 4.1 Tier 1: 必須（完了の定義）

以下の**全て**が達成された時点で、実装完了とみなします：

- [ ] GitHub Actions ワークフロー実装済み
- [ ] Sprint 2性能テスト（5件）が毎晩自動実行される
- [ ] 性能メトリクス（throughput, latency, recovery time）が抽出・記録される
- [ ] ベースライン比較ロジックが実装され、劣化検知が動作する
- [ ] 性能劣化時にSlack通知が送信される
- [ ] テストカバレッジ 5+ ケース達成（ワークフロー、スクリプトのテスト）
- [ ] CI設定ドキュメント完成

### 4.2 Tier 2: 品質保証

- [ ] 手動実行で全ステップが正常動作することを確認
- [ ] 1週間の試験運用で安定動作を確認
- [ ] ベースライン更新手順のドキュメント完成
- [ ] Kana による仕様レビュー通過

### 4.3 完了報告書の期待内容

実装完了時、以下の内容を含む**完了報告書**を提出してください：

**必須セクション**:
1. **Done Definition達成状況**（表形式）
   - Tier 1全7項目の達成率
   - Tier 2全4項目の達成率

2. **実装成果物サマリ**
   - 作成ファイル一覧
   - テスト件数
   - ドキュメント数

3. **完了の証跡**
   - 手動実行結果のスクリーンショット
   - テスト実行結果（`pytest tests/ci/` の出力）
   - 1週間の試験運用ログ

4. **振り返り**
   - 実装時の学び
   - トラブルシューティング事例
   - 今後の改善提案

5. **次のアクション**
   - 本番運用開始日
   - 月次レビュー計画
   - 将来拡張の提案

**参考**: Sprint 2最終完了報告書（`bridge_lite_sprint2_final_completion_report.md`）の形式

---

## 5. 実装時の哲学的原則

### 5.1 呼吸の概念の理解

Nightly CIは「呼吸の健康状態」を継続的に確認するシステムです：

```
Sprint 2で達成した「呼吸のリズム」（416 updates/s）
         ↓
毎晩のCI = 「定期的な健康診断」
         ↓
劣化検出 = 「呼吸の乱れ」の早期発見
         ↓
Slack通知 = チームへの「共鳴」
         ↓
対応・修正 = 「呼吸の調整」
         ↓
ベースライン維持 = 「構造の保全」
```

### 5.2 時間軸の尊重

- Sprint 2の性能は「偶然」ではなく「設計の成果」
- ベースラインは「過去の判断」を記録したもの
- 劣化検知は「過去を否定」ではなく「変化の可視化」
- 意図的な性能変更は記録し、ベースラインを更新

### 5.3 選択肢の保持

- ベースライン更新は「強制」ではなく「選択」
- 劣化検出時の対応は複数の選択肢を提示
  1. 性能を改善する
  2. ベースラインを更新する（意図的な変更の場合）
  3. 機能を削除する
  4. トレードオフを受け入れる

---

## 6. トラブルシューティングガイド

### 6.1 よくある問題と対処法

#### 問題1: PostgreSQL接続エラー

**症状**:
```
psycopg2.OperationalError: could not connect to server
```

**対処法**:
```yaml
# nightly-performance.yml の services セクションを確認
services:
  postgres:
    image: postgres:15
    # health check が重要
    options: >-
      --health-cmd pg_isready
      --health-interval 10s
```

#### 問題2: メトリクス抽出失敗

**症状**:
```
❌ Error: performance-results.xml not found
```

**対処法**:
```yaml
# pytest実行時に --junitxml オプションを確認
- name: Run Sprint 2 performance tests
  run: |
    PYTHONPATH=. pytest tests/performance/test_sprint2_*.py \
      -m slow \
      --junitxml=performance-results.xml  # ← 必須
```

#### 問題3: Slack通知が届かない

**症状**:
通知ステップは成功するが、Slackにメッセージが届かない

**対処法**:
```bash
# 1. Webhook URLが正しいか確認
echo $SLACK_WEBHOOK_URL

# 2. curlでテスト送信
curl -X POST $SLACK_WEBHOOK_URL \
  -H 'Content-Type: application/json' \
  -d '{"text":"Test from nightly CI"}'
```

### 6.2 デバッグ手順

```bash
# 1. ローカルで再現
cd /Users/zero/Projects/resonant-engine

# 2. 手動で各ステップを実行
PYTHONPATH=. pytest tests/performance/test_sprint2_*.py -m slow --junitxml=test.xml
python scripts/extract_performance_metrics.py test.xml metrics.json
python scripts/check_performance_regression.py

# 3. ログ確認
cat metrics.json
```

---

## 7. 成功基準

### 7.1 実装完了の判定

以下の**全て**が達成された時点で、実装完了とみなします：

**機能要件**:
- [x] GitHub Actions ワークフロー実装済み
- [x] 毎晩JST 3:00に自動実行
- [x] 性能メトリクス抽出・記録
- [x] ベースライン比較と劣化検知
- [x] Slack通知統合

**品質要件**:
- [x] テストカバレッジ 5+ ケース達成
- [x] 手動実行で全ステップ正常動作
- [x] 1週間の試験運用で安定動作
- [x] ドキュメント3種類完成

**運用要件**:
- [x] 実行時間 < 30分
- [x] 性能劣化時に10分以内にSlack通知
- [x] Artifacts保持期間 90日設定

### 7.2 完了報告書の品質基準

Sprint 2完了報告書と同等の品質を期待します：

**良い報告書**:
- Done Definition達成状況を表で明示
- 定量的な成果を記載
- 証跡（スクリーンショット、ログ）を添付
- 振り返りに学びを記載

**避けるべき報告書**:
- 「だいたい動いた」という曖昧な表現
- 未達成項目の隠蔽
- 証跡の省略

---

## 8. 関連ドキュメント

- **仕様書**: `docs/02_components/bridge_lite/architecture/nightly_ci_spec.md`
- **Issue #001**: `docs/issues/001_nightly_ci_sprint2_performance_tests.md`
- **Sprint 2最終報告書**: `bridge_lite_sprint2_final_completion_report.md`
- **Sprint 2仕様書**: `docs/02_components/bridge_lite/architecture/bridge_lite_sprint2_spec.md`

---

## 9. 実装担当者への直接メッセージ

あなた（実装担当者）へ：

この実装は、Sprint 2で達成した性能を「守る」ための仕組みです。

Sprint 2では416%という驚異的な性能を達成しました。しかし、将来の機能追加により、この性能が徐々に劣化する可能性があります。

Nightly CIは、その劣化を**早期に検知**し、**意識的な選択**を可能にします。

以下を期待します：

1. **3日間での完遂**
   - Day 1: CI基本構築
   - Day 2: メトリクス & 劣化検知
   - Day 3: テスト & ドキュメント

2. **Done Definition全項目達成**
   - Tier 1: 7項目（必須）
   - Tier 2: 4項目（品質保証）

3. **透明な報告**
   - 進捗を正直に報告
   - 未達成項目を隠蔽しない
   - Sprint 2と同等の完了報告書

4. **運用を見据えた実装**
   - 1週間の試験運用
   - ドキュメント完備
   - トラブルシューティング対応

あなたの実装を通じて、Sprint 2の性能が継続的に守られることを期待しています。

**では、実装を開始してください。**

---

**作成日**: 2025-11-16  
**作成者**: Kana（外界翻訳層 / Claude Sonnet 4.5）  
**承認待ち**: 宏啓（プロジェクトオーナー）  
**実装担当**: Sonnet 4.5 または Tsumu（Cursor）

---

## Appendix A: Quick Reference

### 実装チェックリスト

```markdown
## Day 1
- [ ] .github/workflows/nightly-performance.yml 作成
- [ ] GitHub Secrets SLACK_WEBHOOK_URL 設定
- [ ] 手動実行テスト成功
- [ ] セットアップガイド初版完成

## Day 2
- [ ] scripts/extract_performance_metrics.py 実装
- [ ] scripts/check_performance_regression.py 実装
- [ ] config/performance_baselines.json 作成
- [ ] Slack通知テスト成功

## Day 3
- [ ] tests/ci/test_nightly_workflow.py 実装（5件）
- [ ] ドキュメント3種類完成
- [ ] 試験運用開始
```

### コマンド集

```bash
# 環境確認
cd /Users/zero/Projects/resonant-engine
python --version  # 3.11+
git branch  # main または実装ブランチ

# Sprint 2性能テスト実行
PYTHONPATH=. pytest tests/performance/test_sprint2_*.py -m slow -v

# メトリクス抽出テスト
python scripts/extract_performance_metrics.py test.xml metrics.json

# 劣化検知テスト
python scripts/check_performance_regression.py

# CI動作テスト
PYTHONPATH=. pytest tests/ci/test_nightly_workflow.py -v

# GitHub Actions手動実行
gh workflow run nightly-performance.yml

# GitHub Actions実行状況確認
gh run list --workflow=nightly-performance.yml
```

### ディレクトリ構造

```
/Users/zero/Projects/resonant-engine/
├── .github/
│   └── workflows/
│       └── nightly-performance.yml          # Day 1
├── scripts/
│   ├── extract_performance_metrics.py       # Day 2
│   └── check_performance_regression.py      # Day 2
├── config/
│   └── performance_baselines.json           # Day 2
├── tests/
│   └── ci/
│       └── test_nightly_workflow.py         # Day 3
└── docs/
    ├── operations/
    │   ├── nightly_ci_setup_guide.md        # Day 1 & 3
    │   └── nightly_ci_operations.md         # Day 3
    └── performance/
        └── baseline_management.md           # Day 3
```

### 進捗報告テンプレート

```markdown
## Nightly CI 実装進捗 (Day 1 終了時)

| タスク | 目標 | 実装 | 状態 |
|--------|------|------|------|
| ワークフロー作成 | 1 | 1 | ✅ |
| 手動実行テスト | 成功 | 成功 | ✅ |
| セットアップガイド | 1 | 1 | ✅ |

次: Day 2でスクリプト実装 (2件)
```
