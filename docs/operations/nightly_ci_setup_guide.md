# Nightly CI セットアップガイド

**作成日**: 2025-11-17
**バージョン**: 1.0

---

## 1. 概要

本ガイドでは、Resonant Engine の Memory System 継続的監視のための Nightly CI システムのセットアップ手順を説明します。

### 1.1 システム構成

```
GitHub Actions Nightly CI
├── トリガー: 毎日 JST 3:00 (UTC 18:00)
├── テスト対象:
│   ├── Memory Management System (72 tests)
│   ├── Semantic Bridge System (97 tests)
│   └── Memory Store System (36 tests)
├── メトリクス抽出: scripts/extract_performance_metrics.py
├── 劣化検知: scripts/check_performance_regression.py
├── ベースライン: config/performance_baselines.json
└── 通知: Slack Webhook
```

---

## 2. 前提条件

### 2.1 必要なもの

- GitHub リポジトリ（プッシュ権限あり）
- Slack ワークスペース（通知用）
- Python 3.11+ 環境

### 2.2 リポジトリ構造

以下のファイルが存在すること：

```bash
# 確認コマンド
ls -la .github/workflows/nightly-performance.yml
ls -la scripts/extract_performance_metrics.py
ls -la scripts/check_performance_regression.py
ls -la config/performance_baselines.json
ls -la tests/ci/
```

---

## 3. GitHub Actions 設定

### 3.1 ワークフローファイル確認

`.github/workflows/nightly-performance.yml` が存在し、以下を含むこと：

```yaml
name: Nightly Performance Tests

on:
  schedule:
    - cron: '0 18 * * *'  # JST 3:00
  workflow_dispatch:  # 手動実行
```

### 3.2 GitHub Actions 有効化

1. リポジトリの **Settings** → **Actions** → **General**
2. "Allow all actions and reusable workflows" を選択
3. "Save" をクリック

### 3.3 Secrets 設定（Slack 通知用）

1. **Settings** → **Secrets and variables** → **Actions**
2. **New repository secret** をクリック
3. 以下を設定：

| Name | Value |
|------|-------|
| `SLACK_WEBHOOK_URL` | Slack Incoming Webhook URL |

#### Slack Webhook URL 取得方法

1. [Slack API](https://api.slack.com/apps) にアクセス
2. **Create New App** → **From scratch**
3. **Incoming Webhooks** を有効化
4. **Add New Webhook to Workspace**
5. 通知先チャンネルを選択
6. Webhook URL をコピー（`https://hooks.slack.com/services/...`）

---

## 4. 初回実行テスト

### 4.1 手動実行（推奨）

1. GitHub リポジトリの **Actions** タブ
2. **Nightly Performance Tests** ワークフロー選択
3. **Run workflow** → **Run workflow** をクリック
4. 実行状況を監視

### 4.2 実行結果確認

成功時の期待結果：

- ✅ "Set up Python 3.11" 成功
- ✅ "Install dependencies" 成功
- ✅ "Run Memory System Tests" 205+ テストパス
- ✅ "Extract performance metrics" JSON 生成
- ✅ "Check for performance regression" exit 0
- ✅ Artifacts アップロード成功

### 4.3 Artifacts 確認

1. ワークフロー実行の **Summary** ページ
2. **Artifacts** セクション確認
3. `performance-test-results-{run_number}` ダウンロード

含まれるファイル：
- `performance-results.xml` - JUnit テスト結果
- `performance-metrics.json` - 抽出されたメトリクス
- `test-report.json` - pytest JSON レポート
- `coverage.json` - カバレッジデータ

---

## 5. ローカルテスト（CI実行前確認）

### 5.1 CI インフラテスト

```bash
# プロジェクトルートで実行
cd /path/to/resonant-engine
export PYTHONPATH=$(pwd)

# CI テスト実行（13+テスト）
python -m pytest tests/ci/ -v

# 期待結果: 13+ passed
```

### 5.2 メトリクス抽出テスト

```bash
# Memory System テスト実行
python -m pytest tests/memory/ tests/semantic_bridge/ tests/test_memory_store/ \
  --junitxml=test-results.xml -v

# メトリクス抽出
python scripts/extract_performance_metrics.py \
  test-results.xml \
  nonexistent.json \
  performance-metrics.json

# 結果確認
cat performance-metrics.json | python -m json.tool
```

### 5.3 劣化検知テスト

```bash
# 正常パターン（劣化なし）
python scripts/check_performance_regression.py
# 期待: exit 0, "No performance regression detected"
```

---

## 6. スケジュール実行確認

### 6.1 cron スケジュール

```yaml
schedule:
  - cron: '0 18 * * *'  # 毎日 UTC 18:00 = JST 3:00
```

### 6.2 実行履歴確認

1. **Actions** → **Nightly Performance Tests**
2. 過去の実行履歴を確認
3. cron 実行は "schedule" トリガーとして表示

### 6.3 注意事項

- GitHub Actions の cron は正確ではない（数分の遅延あり）
- デフォルトブランチ（main/master）でのみ動作
- ワークフローが60日間実行されないと自動無効化

---

## 7. トラブルシューティング

### 7.1 ワークフローが実行されない

**原因**: デフォルトブランチにワークフローファイルがない

**対処**:
```bash
git checkout main
git merge feature-branch
git push origin main
```

### 7.2 テスト失敗

**確認事項**:
1. 依存関係は最新か？（`requirements.txt`）
2. Python バージョンは正しいか？（3.11+）
3. テストコード自体にエラーがないか？

**ローカル再現**:
```bash
pip install -r requirements.txt
python -m pytest tests/memory/ tests/semantic_bridge/ tests/test_memory_store/ -v
```

### 7.3 Slack 通知が届かない

**確認事項**:
1. `SLACK_WEBHOOK_URL` シークレットが設定されているか？
2. Webhook URL が有効か？
3. ワークフローが失敗しているか？（成功時は通知されない）

**テスト送信**:
```bash
curl -X POST $SLACK_WEBHOOK_URL \
  -H 'Content-Type: application/json' \
  -d '{"text":"Test from Nightly CI"}'
```

### 7.4 メトリクス抽出エラー

**エラー**: `Error: performance-results.xml not found`

**対処**: pytest 実行時に `--junitxml` オプションを確認

```yaml
# ワークフロー内
--junitxml=performance-results.xml
```

---

## 8. 設定カスタマイズ

### 8.1 実行時刻変更

```yaml
schedule:
  - cron: '0 15 * * *'  # UTC 15:00 = JST 24:00
```

### 8.2 テスト対象追加

```yaml
- name: Run Memory System Tests
  run: |
    python -m pytest tests/memory/ tests/semantic_bridge/ tests/test_memory_store/ \
      tests/NEW_MODULE/ \  # 新規モジュール追加
      -v --junitxml=performance-results.xml
```

### 8.3 ベースライン調整

`config/performance_baselines.json` を編集：

```json
{
  "memory_system": {
    "thresholds": {
      "total_tests": {
        "min": 250,  // テスト追加後に更新
        "warning_threshold": 0.95
      }
    }
  }
}
```

---

## 9. 運用開始チェックリスト

- [ ] GitHub Actions 有効化確認
- [ ] Slack Webhook URL シークレット設定
- [ ] 手動実行テスト成功
- [ ] Artifacts 生成確認
- [ ] ローカル CI テストパス（13+件）
- [ ] ベースライン設定確認
- [ ] ドキュメント整備完了
- [ ] チームへの周知

---

## 10. 次のステップ

1. **試験運用開始**: 1週間の安定動作確認
2. **月次レビュー設定**: メトリクス履歴分析
3. **ベースライン更新**: 新機能追加時の調整
4. **拡張計画**: ダッシュボード構築（将来）

---

**作成日**: 2025-11-17
**作成者**: Sonnet 4.5（Claude Code）
