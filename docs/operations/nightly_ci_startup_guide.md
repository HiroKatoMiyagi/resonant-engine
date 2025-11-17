# Nightly CI 運用開始ガイド

**作成日**: 2025年11月17日  
**対象**: Resonant Engine Nightly CI  
**目的**: 本格運用開始のステップバイステップガイド

---

## 📋 実施計画

### Phase 1: 即座実施（今日）
1. ✅ GitHub Actions手動実行テスト - **完了 (11/17 実行ID: 19424424182)**
2. ⏸️ Slack Webhook設定 - **後回し（通知不要）**

### Phase 2: 試験運用（1週間）
3. ⏳ 毎日の実行結果監視 - **開始準備完了**
4. ⏳ 問題点の洗い出し

### Phase 3: 本格運用（1ヶ月〜）
5. ⏳ 月次レビュー設定
6. ⏳ メトリクストレンド分析

---

## 1. GitHub Actions手動実行テスト

### 1.1 前提確認

```bash
# 現在のブランチ確認
cd /Users/zero/Projects/resonant-engine
git branch
# 期待: * main

# リモートにプッシュ
git push origin main
```

---

### 1.2 GitHub UIから手動実行

#### ステップ1: GitHub Actionsページへ移動

1. ブラウザで開く: https://github.com/HiroKatoMiyagi/resonant-engine/actions
2. 左サイドバーから **"Nightly Performance Tests"** をクリック

#### ステップ2: 手動実行

1. 右上の **"Run workflow"** ボタンをクリック
2. ブランチ選択: **main** (デフォルト)
3. **"Run workflow"** 緑ボタンをクリック

#### ステップ3: 実行状況確認

- ワークフロー実行が開始される（黄色●表示）
- クリックして詳細画面へ
- 各ステップの進行状況をリアルタイム確認

**期待される実行時間**: 5-10分

---

### 1.3 CLI（GitHub CLI）から手動実行

```bash
# GitHub CLIインストール確認
gh --version

# 未インストールの場合
brew install gh
gh auth login

# ワークフロー手動実行
cd /Users/zero/Projects/resonant-engine
gh workflow run "Nightly Performance Tests" --ref main

# 実行状況確認
gh run list --workflow=nightly-performance.yml --limit 5

# リアルタイム監視
gh run watch
```

---

### 1.4 実行結果（2025年11月17日）

**✅ 手動実行テスト成功**

- **実行ID**: 19424424182
- **所要時間**: 24秒
- **ステータス**: ✅ 成功

**成功したステップ**:
- ✅ Checkout code
- ✅ Set up Python 3.11
- ✅ Install dependencies
- ✅ Run Memory System Tests
- ✅ Extract performance metrics
- ✅ Check for performance regression
- ✅ Upload test results
- ✅ Create summary

**Slack通知**: ⏸️ 現時点では設定せず（後回し）

**結論**: ワークフローは正常に動作しており、毎日JST 3:00の自動実行が可能。

---

## 2. Slack Webhook設定（オプション - 現在スキップ）

> **注意**: 2025年11月17日時点でSlack通知は不要と判断。  
> 必要になった場合は以下の手順で設定可能。

### 2.1 Slack Webhook URL取得

#### ステップ1: Slack Appを作成

1. https://api.slack.com/apps にアクセス
2. **"Create New App"** → **"From scratch"**
3. App名: `Resonant Engine CI`
4. Workspace選択: あなたのワークスペース
5. **"Create App"** をクリック

#### ステップ2: Incoming Webhooksを有効化

1. 左サイドバー **"Incoming Webhooks"** をクリック
2. **"Activate Incoming Webhooks"** をONに切り替え
3. 下部の **"Add New Webhook to Workspace"** をクリック
4. 通知先チャンネル選択（例: `#ci-notifications`）
5. **"Allow"** をクリック

#### ステップ3: Webhook URLをコピー

```
https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX
```

このURLを安全に保管してください。

---

### 2.2 GitHub Secretsに追加

#### 方法1: GitHub CLIから（推奨）

```bash
cd /Users/zero/Projects/resonant-engine

# Webhook URLを一時的に環境変数に設定
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."

# GitHub Secretsに追加
gh secret set SLACK_WEBHOOK_URL --body "$SLACK_WEBHOOK_URL"

# 確認
gh secret list
# 期待: SLACK_WEBHOOK_URL (Updated 2025-11-17)
```

#### 方法2: GitHub UIから

1. https://github.com/HiroKatoMiyagi/resonant-engine/settings/secrets/actions にアクセス
2. **"New repository secret"** をクリック
3. 入力:
   - Name: `SLACK_WEBHOOK_URL`
   - Secret: `https://hooks.slack.com/services/...`
4. **"Add secret"** をクリック

---

### 2.3 Slack通知の動作確認

**既存実装**: ワークフローに既に実装済み
- テスト失敗時の通知
- リグレッション検出時の通知

**動作確認手順**:
1. `SLACK_WEBHOOK_URL`シークレット設定後
2. GitHub Actionsを手動実行
3. Slackチャンネルに通知が届くことを確認

---

## 3. 1週間試験運用

### 3.1 日次監視（毎朝JST 9:00頃）

```bash
# 最新実行結果確認
gh run list --workflow=nightly-performance.yml --limit 1

# 詳細ログ表示
gh run view --log
```

**チェック項目**:
- [ ] ワークフロー実行成功/失敗
- [ ] テスト通過率
- [ ] リグレッション検出有無
- [ ] 実行時間（目標: < 10分）
- [ ] Slack通知動作確認

---

### 3.2 監視スプレッドシート（推奨）

**Google Spreadsheetsで記録**:

| 日付 | 実行時刻 | ステータス | テスト数 | 通過率 | 実行時間 | リグレッション | 備考 |
|------|---------|----------|---------|--------|---------|--------------|------|
| 11/18 | 03:00 | ✅ | 205 | 100% | 8m32s | なし | 初回実行 |
| 11/19 | 03:00 | ✅ | 205 | 100% | 8m45s | なし | - |
| ... | ... | ... | ... | ... | ... | ... | ... |

---

### 3.3 週次レビュー（金曜日）

**レビューミーティング議題**:
1. 今週の実行サマリー
   - 成功率: X/7 (XX%)
   - 平均実行時間: Xm Ys
   - リグレッション回数: X回
2. 検出した問題と対応
3. ベースライン更新の必要性
4. ワークフロー改善提案

---

## 4. 月次レビュー設定

### 4.1 メトリクストレンド分析スクリプト

```python
# scripts/analyze_performance_trends.py

import json
import glob
from datetime import datetime
import matplotlib.pyplot as plt

def analyze_trends():
    """過去30日の性能トレンド分析"""
    
    metrics_files = sorted(glob.glob('metrics/*.json'))
    
    dates = []
    test_counts = []
    pass_rates = []
    execution_times = []
    
    for file in metrics_files:
        with open(file) as f:
            data = json.load(f)
            
        dates.append(data['timestamp'])
        test_counts.append(data['total_tests'])
        pass_rates.append(data['pass_rate'] * 100)
        execution_times.append(data['execution_time_seconds'])
    
    # グラフ生成
    fig, axes = plt.subplots(3, 1, figsize=(12, 10))
    
    axes[0].plot(dates, test_counts, marker='o')
    axes[0].set_title('Test Count Trend')
    axes[0].axhline(y=205, color='r', linestyle='--', label='Baseline')
    
    axes[1].plot(dates, pass_rates, marker='o', color='green')
    axes[1].set_title('Pass Rate Trend')
    axes[1].axhline(y=95, color='r', linestyle='--', label='Threshold')
    
    axes[2].plot(dates, execution_times, marker='o', color='orange')
    axes[2].set_title('Execution Time Trend')
    
    plt.tight_layout()
    plt.savefig('reports/performance_trends.png')
    print('✅ Trend analysis saved')

if __name__ == '__main__':
    analyze_trends()
```

---

### 4.2 月次レビュー会議テンプレート

```markdown
# Nightly CI 月次レビュー - YYYY年MM月

**開催日**: YYYY-MM-DD  
**参加者**: [名前]  
**レビュー期間**: YYYY-MM-01 〜 YYYY-MM-31

---

## 1. 実行サマリー

| 指標 | 値 | 前月比 |
|------|-----|--------|
| **総実行回数** | XX回 | +X% |
| **成功率** | XX% | +X% |
| **平均実行時間** | Xm Ys | -X% |

## 2. トレンド分析

![Performance Trends](../reports/performance_trends.png)

## 3. 改善提案

- [ ] Sprint 4ベースライン追加
- [ ] 実行時間最適化
- [ ] アラート閾値見直し

---

**次回レビュー**: YYYY-MM-DD
```

---

## 5. 実施チェックリスト

### Phase 1: 今日実施 ✅

- [x] **1. GitHub CLI インストール**
  ```bash
  brew install gh
  gh auth login
  ```

- [x] **2. GitHub Actions手動実行**
  ```bash
  gh workflow run "Nightly Performance Tests" --ref main
  gh run watch
  ```
  **結果**: ✅ 成功 (実行ID: 19424424182, 所要時間: 24秒)

- [x] **3. 実行結果確認**
  - ✅ Memory System Tests: 全テスト通過
  - ✅ Performance metrics: 抽出成功
  - ✅ Regression check: 異常なし

- [ ] **4. Slack Webhook設定** - ⏸️ **スキップ（現時点で不要）**

---

### Phase 2: 試験運用（11/18〜11/24）⏳

- [ ] **月曜 (11/18)**: 初回自動実行確認
- [ ] **火〜木**: 毎日実行結果記録
- [ ] **金曜 (11/22)**: 週次レビュー実施
- [ ] **土日**: 実行結果記録

---

### Phase 3: 本格運用（12月〜）⏳

- [ ] **12/1**: Sprint 4ベースライン追加
- [ ] **12/15**: 月次レビュー実施
- [ ] **継続**: 毎日の監視、週次・月次レビュー

---

## 6. トラブルシューティング

### Q1: Slack通知が届かない

**確認項目**:
```bash
gh secret list | grep SLACK
```

**対処**:
```bash
gh secret delete SLACK_WEBHOOK_URL
gh secret set SLACK_WEBHOOK_URL --body "新しいURL"
```

---

### Q2: テスト数がベースラインと一致しない

**対処**:
```bash
vi config/performance_baselines.json
# memory_store.tests を 36 → 41 に変更
# retrieval_orchestrator セクション追加
```

---

## 7. 参考リソース

- **GitHub Actions Docs**: https://docs.github.com/en/actions
- **Slack Incoming Webhooks**: https://api.slack.com/messaging/webhooks
- **既存ドキュメント**:
  - `docs/operations/nightly_ci_setup_guide.md`
  - `docs/operations/nightly_ci_operations.md`
  - `docs/performance/baseline_management.md`

---

**作成者**: GitHub Copilot  
**更新日**: 2025年11月17日
