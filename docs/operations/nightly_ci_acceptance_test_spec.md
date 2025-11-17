# Nightly CI システム ローカル受け入れテスト仕様書

**作成日**: 2025-11-17
**作成者**: Sonnet 4.5（Claude Code / 補助具現層）
**対象システム**: Nightly Performance CI for Memory System
**バージョン**: 1.0

---

## 1. 概要

### 1.1 目的

本仕様書は、Nightly CI システムのローカル環境での受け入れテストを定義する。GitHub Actions環境を使用せずに、CI インフラストラクチャの完全性と正確性を検証する。

### 1.2 背景

Memory System（Sprint 1-3）の継続的監視のため、以下のベースラインを保護する：

| コンポーネント | テスト数 | 性能指標 |
|--------------|---------|---------|
| Memory Management (Sprint 1) | 72 | 実行時間 0.36s |
| Semantic Bridge (Sprint 2) | 97 | 0.12ms/event, 推論精度 100% |
| Memory Store (Sprint 3) | 36 | - |
| **合計** | **205** | - |

### 1.3 テスト範囲

**IN Scope**:
- CI インフラファイルの存在確認
- メトリクス抽出スクリプトの機能テスト
- 劣化検知スクリプトの機能テスト
- ベースライン設定の整合性検証
- 手動実行シミュレーション

**OUT of Scope**:
- GitHub Actions 実環境でのテスト
- Slack 通知の実際の送信確認
- PostgreSQL 連携テスト（In-Memory のみ）

---

## 2. テスト環境要件

### 2.1 ハードウェア/OS

- Ubuntu Linux または macOS
- Python 3.11+
- Git

### 2.2 依存パッケージ

```bash
pip install pytest pytest-asyncio pyyaml
```

### 2.3 プロジェクト構造

```
resonant-engine/
├── .github/workflows/nightly-performance.yml
├── scripts/
│   ├── extract_performance_metrics.py
│   └── check_performance_regression.py
├── config/
│   └── performance_baselines.json
├── tests/ci/
│   ├── __init__.py
│   └── test_nightly_workflow.py
└── docs/operations/
    └── nightly_ci_acceptance_test_spec.md
```

---

## 3. 受け入れ基準（Acceptance Criteria）

### 3.1 Tier 1: 必須基準

以下の**全て**が達成されること：

| # | 基準 | 検証方法 | 期待結果 |
|---|------|---------|---------|
| 1 | CIワークフローファイル存在 | ファイルパス確認 | `.github/workflows/nightly-performance.yml` 存在 |
| 2 | メトリクス抽出スクリプト動作 | 手動実行 | JUnit XML → JSON 変換成功 |
| 3 | 劣化検知スクリプト動作 | 正常メトリクス投入 | exit 0, "No regression" |
| 4 | 劣化検知（低テスト数）| 低テスト数投入 | exit 1, "REGRESSION" |
| 5 | 劣化検知（低パス率）| 低パス率投入 | exit 1, "REGRESSION" |
| 6 | ベースライン設定整合性 | 設定値確認 | Sprint報告書と一致 |
| 7 | CIテスト全件パス | pytest実行 | 13+ tests passed |

### 3.2 Tier 2: 品質基準

| # | 基準 | 検証方法 | 期待結果 |
|---|------|---------|---------|
| 1 | YAML構文妥当性 | yaml.safe_load | エラーなし |
| 2 | スクリプト実行速度 | タイムアウト確認 | < 30秒 |
| 3 | エラーハンドリング | 不正入力テスト | 適切なエラーメッセージ |
| 4 | ドキュメント完備 | ファイル存在確認 | 3種類のドキュメント |

---

## 4. テスト実行手順

### 4.1 事前準備

```bash
# 1. リポジトリルートに移動
cd /path/to/resonant-engine

# 2. 依存関係インストール
pip install pytest pytest-asyncio pyyaml

# 3. 環境変数設定
export PYTHONPATH=$(pwd)
```

### 4.2 自動テスト実行

```bash
# CI インフラテスト実行（13+テストケース）
python -m pytest tests/ci/ -v

# 期待結果:
# ======================== 13 passed, X warnings in 0.XXs =========================
```

**テストケース内訳**:

1. `test_extract_metrics_script_exists` - メトリクス抽出スクリプト存在
2. `test_regression_check_script_exists` - 劣化検知スクリプト存在
3. `test_baseline_config_exists` - ベースライン設定ファイル存在
4. `test_baseline_config_structure` - 設定構造妥当性
5. `test_github_workflow_exists` - GitHub Actionsワークフロー存在
6. `test_github_workflow_valid_yaml` - YAML構文妥当性
7. `test_extract_metrics_script_runs_with_mock_data` - メトリクス抽出機能
8. `test_extract_metrics_handles_failures` - 失敗テスト処理
9. `test_regression_check_no_regression` - 正常パターン検知
10. `test_regression_check_detects_low_test_count` - 低テスト数検知
11. `test_regression_check_detects_low_pass_rate` - 低パス率検知
12. `test_baseline_values_match_sprint_reports` - Sprint報告書整合性
13. `test_total_test_count_baseline` - 総テスト数計算

### 4.3 手動メトリクス抽出テスト

```bash
# 1. Memory Systemテスト実行（実際のテスト）
python -m pytest tests/memory/ tests/semantic_bridge/ tests/test_memory_store/ \
  --junitxml=test-results.xml \
  -v

# 2. メトリクス抽出
python scripts/extract_performance_metrics.py \
  test-results.xml \
  nonexistent.json \
  performance-metrics.json

# 3. 結果確認
cat performance-metrics.json | python -m json.tool
```

**期待出力例**:
```json
{
  "timestamp": "2025-11-17T12:00:00.000000+00:00",
  "tests_total": 205,
  "tests_passed": 205,
  "tests_failed": 0,
  "memory_management_tests": 72,
  "semantic_bridge_tests": 97,
  "memory_store_tests": 36,
  "inference_accuracy": 100.0,
  "processing_performance_ms": 0.12,
  "all_tests_passed": true
}
```

### 4.4 手動劣化検知テスト

#### パターン A: 正常（劣化なし）

```bash
# 正常なメトリクスを作成
cat > performance-metrics.json << 'EOF'
{
  "tests_total": 205,
  "tests_passed": 205,
  "tests_failed": 0,
  "memory_management_tests": 72,
  "semantic_bridge_tests": 97,
  "memory_store_tests": 36,
  "inference_accuracy": 100.0,
  "processing_performance_ms": 0.12
}
EOF

# 劣化検知実行
python scripts/check_performance_regression.py
echo "Exit code: $?"

# 期待結果:
# No performance regression detected
# Exit code: 0
```

#### パターン B: 劣化（低テスト数）

```bash
# 低テスト数のメトリクス
cat > performance-metrics.json << 'EOF'
{
  "tests_total": 150,
  "tests_passed": 150,
  "tests_failed": 0,
  "memory_management_tests": 50,
  "semantic_bridge_tests": 70,
  "memory_store_tests": 30,
  "inference_accuracy": 100.0,
  "processing_performance_ms": 0.12
}
EOF

python scripts/check_performance_regression.py
echo "Exit code: $?"

# 期待結果:
# PERFORMANCE REGRESSION DETECTED
# REGRESSION: Total Tests
# Exit code: 1
```

#### パターン C: 劣化（低推論精度）

```bash
# 低推論精度のメトリクス
cat > performance-metrics.json << 'EOF'
{
  "tests_total": 205,
  "tests_passed": 205,
  "tests_failed": 0,
  "memory_management_tests": 72,
  "semantic_bridge_tests": 97,
  "memory_store_tests": 36,
  "inference_accuracy": 60.0,
  "processing_performance_ms": 0.12
}
EOF

python scripts/check_performance_regression.py
echo "Exit code: $?"

# 期待結果:
# PERFORMANCE REGRESSION DETECTED
# REGRESSION: Inference Accuracy
# Exit code: 1
```

### 4.5 ベースライン設定検証

```bash
# ベースライン設定の読み込みと検証
python << 'EOF'
import json

with open('config/performance_baselines.json') as f:
    baselines = json.load(f)

# Sprint報告書との整合性確認
components = baselines['memory_system']['components']
thresholds = baselines['memory_system']['thresholds']

print("=== Component Baseline Verification ===")
print(f"Memory Management: {components['memory_management']['tests']} tests (Expected: 72)")
print(f"Semantic Bridge: {components['semantic_bridge']['tests']} tests (Expected: 97)")
print(f"Memory Store: {components['memory_store']['tests']} tests (Expected: 36)")
print(f"Total: {thresholds['total_tests']['min']} tests (Expected: 205)")
print()

# 閾値設定確認
print("=== Threshold Configuration ===")
print(f"Total Tests Warning: {thresholds['total_tests']['warning_threshold']*100}%")
print(f"Pass Rate Minimum: {thresholds['test_pass_rate']['min']*100}%")
print(f"Inference Accuracy Minimum: {thresholds['inference_accuracy']['min']}%")
print(f"Processing Performance Max: {thresholds['processing_performance_ms']['max']}ms")
print()

# 検証
assert components['memory_management']['tests'] == 72
assert components['semantic_bridge']['tests'] == 97
assert components['memory_store']['tests'] == 36
assert thresholds['total_tests']['min'] == 205
print("✅ All baseline values match Sprint reports!")
EOF
```

---

## 5. テスト結果記録テンプレート

### 5.1 自動テスト結果

```markdown
## Nightly CI 受け入れテスト結果
**実行日時**: YYYY-MM-DD HH:MM:SS
**実行者**:
**環境**: Python X.X, OS Name

### 自動テスト
- **Total**: XX tests
- **Passed**: XX
- **Failed**: XX
- **Warnings**: XX
- **実行時間**: X.XXs

### 詳細結果

| テストケース | 状態 | 備考 |
|-------------|------|------|
| test_extract_metrics_script_exists | ✅ PASS | |
| test_regression_check_script_exists | ✅ PASS | |
| test_baseline_config_exists | ✅ PASS | |
| test_baseline_config_structure | ✅ PASS | |
| test_github_workflow_exists | ✅ PASS | |
| test_github_workflow_valid_yaml | ✅ PASS | |
| test_extract_metrics_script_runs_with_mock_data | ✅ PASS | |
| test_extract_metrics_handles_failures | ✅ PASS | |
| test_regression_check_no_regression | ✅ PASS | |
| test_regression_check_detects_low_test_count | ✅ PASS | |
| test_regression_check_detects_low_pass_rate | ✅ PASS | |
| test_baseline_values_match_sprint_reports | ✅ PASS | |
| test_total_test_count_baseline | ✅ PASS | |
```

### 5.2 手動テスト結果

```markdown
### 手動テスト

| テストシナリオ | 期待結果 | 実測結果 | 状態 |
|--------------|---------|---------|------|
| メトリクス抽出（正常） | JSON出力成功 | | ☐ |
| 劣化検知（正常） | exit 0, "No regression" | | ☐ |
| 劣化検知（低テスト数） | exit 1, "REGRESSION" | | ☐ |
| 劣化検知（低パス率） | exit 1, "REGRESSION" | | ☐ |
| ベースライン整合性 | Sprint報告書一致 | | ☐ |
```

---

## 6. Done Definition チェックリスト

### 6.1 機能要件

- [ ] GitHub Actions ワークフローファイル作成済み
- [ ] メトリクス抽出スクリプト実装済み
- [ ] 劣化検知スクリプト実装済み
- [ ] ベースライン設定ファイル作成済み
- [ ] CIテスト 13件実装済み
- [ ] 全CIテストがパス

### 6.2 品質要件

- [ ] JUnit XML解析が正常動作
- [ ] 劣化検知が正常/異常パターンを正しく判定
- [ ] ベースライン値がSprint報告書と一致
- [ ] スクリプト実行速度が許容範囲内

### 6.3 ドキュメント要件

- [ ] 受け入れテスト仕様書作成（本ドキュメント）
- [ ] CIセットアップガイド作成
- [ ] ベースライン管理手順書作成
- [ ] 運用手順書作成

---

## 7. トラブルシューティング

### 7.1 テスト失敗時の対処

#### 問題: `test_baseline_config_structure` 失敗

```
AssertionError: memory_management_tests threshold missing
```

**原因**: `config/performance_baselines.json` の構造が不完全

**対処**:
```bash
# ベースライン設定を確認
python -m json.tool config/performance_baselines.json | head -50

# 必要なキーを追加
```

#### 問題: メトリクス抽出スクリプトエラー

```
Error: performance-results.xml not found
```

**対処**:
```bash
# JUnit XML生成を確認
ls -la *.xml

# テスト実行時に --junitxml オプションを使用
python -m pytest tests/ --junitxml=test-results.xml
```

#### 問題: YAML解析エラー

```
yaml.scanner.ScannerError: mapping values are not allowed here
```

**対処**:
```bash
# YAML構文チェック
python -c "import yaml; yaml.safe_load(open('.github/workflows/nightly-performance.yml'))"

# インデントを確認（スペース2つ）
```

### 7.2 環境依存問題

| 問題 | 原因 | 対処 |
|------|------|------|
| `ModuleNotFoundError: pytest` | pytest未インストール | `pip install pytest` |
| `ModuleNotFoundError: yaml` | PyYAML未インストール | `pip install pyyaml` |
| `FileNotFoundError: scripts/...` | 作業ディレクトリ不正 | `cd /path/to/resonant-engine` |

---

## 8. 拡張テスト（オプション）

### 8.1 負荷テスト

```bash
# 大量テストケースでのメトリクス抽出
python << 'EOF'
import subprocess
import time

# 1000テストケースのJUnit XMLを生成
xml_content = '''<?xml version="1.0" encoding="utf-8"?>
<testsuite name="pytest" errors="0" failures="0" tests="1000" time="10.0">
'''
for i in range(1000):
    xml_content += f'<testcase classname="tests.memory.test_{i}" name="test_{i}" time="0.01"/>\n'
xml_content += '</testsuite>'

with open('large-test-results.xml', 'w') as f:
    f.write(xml_content)

start = time.time()
subprocess.run(['python', 'scripts/extract_performance_metrics.py',
                'large-test-results.xml', 'none.json', 'large-metrics.json'],
               capture_output=True)
elapsed = time.time() - start

print(f"Processing time for 1000 tests: {elapsed:.2f}s")
assert elapsed < 5.0, "Processing too slow"
EOF
```

### 8.2 エッジケーステスト

```bash
# 空のJUnit XML
echo '<?xml version="1.0"?><testsuite tests="0"></testsuite>' > empty.xml
python scripts/extract_performance_metrics.py empty.xml none.json empty-metrics.json

# 不正なJSON（メトリクスファイル）
echo '{"invalid": }' > invalid-metrics.json
python scripts/check_performance_regression.py || echo "Expected to fail"
```

---

## 9. 承認欄

### 9.1 テスト実施者

- **氏名**:
- **日付**:
- **全自動テスト結果**: ☐ PASS / ☐ FAIL
- **全手動テスト結果**: ☐ PASS / ☐ FAIL

### 9.2 レビュアー

- **氏名**:
- **日付**:
- **判定**: ☐ 承認 / ☐ 条件付き承認 / ☐ 差し戻し

**コメント**:
```
（レビューコメント）
```

---

## 10. 次のアクション

### 10.1 受け入れテスト合格後

1. **GitHub Actions 実環境テスト**
   - workflow_dispatch で手動実行
   - cron スケジュール確認

2. **Slack 通知設定**
   - SLACK_WEBHOOK_URL シークレット設定
   - テスト通知送信

3. **試験運用開始**
   - 1週間の安定動作確認
   - メトリクス履歴蓄積

### 10.2 継続的改善

- ベースライン更新手順の確立
- 新機能追加時のテスト数調整
- 性能劣化時の対応フロー整備

---

**作成日**: 2025-11-17
**作成者**: Sonnet 4.5（Claude Code / 補助具現層）
**バージョン**: 1.0
