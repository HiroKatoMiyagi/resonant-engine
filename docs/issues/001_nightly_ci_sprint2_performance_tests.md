# Issue #001: Nightly CI に Sprint 2 性能テスト追加

**作成日**: 2025-11-15  
**発行者**: Kana（外界翻訳層）  
**優先度**: P2 (Medium)  
**ステータス**: Open  
**ラベル**: CI/CD, Performance, Sprint 2  
**マイルストーン**: Operations Excellence

---

## 概要

Sprint 2で実装された並行実行制御の性能テスト（`pytest -m slow`）をNightly CIパイプラインに統合し、継続的なパフォーマンス監視を実現する。

---

## 背景

### Sprint 2 完了時の状況

Sprint 2の最終完了報告書（2025-11-15承認）で以下が達成されました：

| テストカテゴリ | テスト数 | 主要メトリクス |
|---------------|---------|---------------|
| 性能テスト基本 | 3件 | Throughput 416 updates/s, P95 latency 0.3ms |
| 性能エッジケース | 2件 | Sustained load, Deadlock recovery <1s |

**合計**: 5件の性能テスト（`tests/performance/test_sprint2_*.py`）

### 現在の課題

1. **手動実行のみ**: 性能テストは開発者が手動で実行
2. **性能劣化の検知遅延**: リグレッションが merge 後に発覚する可能性
3. **CI統合なし**: Nightly CI に性能テストが含まれていない

### なぜ今対応すべきか

- Sprint 2で416%の性能達成を実現したが、将来的な劣化を継続監視する必要がある
- Sprint 3以降の機能追加が性能に影響を与える可能性がある
- 性能テストは時間がかかるため（`pytest -m slow`）、Nightly CI での実行が適切

---

## 目的

### 主要目標

1. **継続的な性能監視**: 毎晩自動実行で性能劣化を早期検知
2. **性能メトリクスの記録**: 時系列での性能トレンドを可視化
3. **性能劣化時のアラート**: 閾値を下回った場合に通知

### 成功基準

- [ ] Nightly CI で `pytest -m slow` が自動実行される
- [ ] 性能メトリクス（throughput, latency）がCI結果に記録される
- [ ] 性能劣化（20%以上の低下）時にSlack通知が送信される
- [ ] ドキュメント（CI設定ガイド）が更新される

---

## 提案する実装

### Phase 1: CI統合基本（1-2時間）

#### 1.1 GitHub Actions ワークフロー作成

**ファイル**: `.github/workflows/nightly-performance.yml`

```yaml
name: Nightly Performance Tests

on:
  schedule:
    # 毎日 JST 3:00 (UTC 18:00) に実行
    - cron: '0 18 * * *'
  workflow_dispatch:  # 手動実行も可能

jobs:
  performance:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: resonant
          POSTGRES_PASSWORD: test_password
          POSTGRES_DB: resonant_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Python 3.11
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov
      
      - name: Run Sprint 2 performance tests
        env:
          DATABASE_URL: postgresql://resonant:test_password@localhost:5432/resonant_test
        run: |
          PYTHONPATH=. pytest tests/performance/test_sprint2_*.py \
            -m slow \
            -v \
            --junitxml=performance-results.xml \
            --cov=bridge/core \
            --cov-report=term \
            --tb=short
      
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: performance-test-results
          path: performance-results.xml
      
      - name: Notify Slack on failure
        if: failure()
        uses: slackapi/slack-github-action@v1
        with:
          webhook-url: ${{ secrets.SLACK_WEBHOOK_URL }}
          payload: |
            {
              "text": "⚠️ Nightly performance tests failed",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*Nightly Performance Tests Failed*\n\nSprint 2 performance tests detected regression.\n\n<${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}|View Details>"
                  }
                }
              ]
            }
```

#### 1.2 pytest マーカー設定確認

**ファイル**: `pytest.ini` または `pyproject.toml`

```ini
[tool.pytest.ini_options]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
]
```

**確認コマンド**:
```bash
# Sprint 2 性能テストがslowマーカーを持つことを確認
grep -r "@pytest.mark.slow" tests/performance/test_sprint2_*.py
```

### Phase 2: メトリクス記録（2-3時間）

#### 2.1 性能メトリクス抽出スクリプト

**ファイル**: `scripts/extract_performance_metrics.py`

```python
#!/usr/bin/env python3
"""Extract performance metrics from pytest output"""
import json
import re
import sys
from pathlib import Path

def extract_metrics(junit_xml_path: str) -> dict:
    """Extract performance metrics from JUnit XML"""
    # JUnit XMLをパースして性能メトリクスを抽出
    # 例: throughput, P95 latency, deadlock recovery time
    
    metrics = {
        "timestamp": "2025-11-15T15:04:00Z",
        "throughput_updates_per_sec": 416,
        "p95_latency_ms": 0.3,
        "deadlock_recovery_sec": 0.8,
        "tests_passed": 5,
        "tests_failed": 0,
    }
    return metrics

def save_metrics(metrics: dict, output_path: str):
    """Save metrics to JSON file"""
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)

if __name__ == "__main__":
    junit_xml = sys.argv[1] if len(sys.argv) > 1 else "performance-results.xml"
    output_json = sys.argv[2] if len(sys.argv) > 2 else "performance-metrics.json"
    
    metrics = extract_metrics(junit_xml)
    save_metrics(metrics, output_json)
    print(f"Metrics extracted to {output_json}")
```

#### 2.2 CI ワークフローへの統合

```yaml
      - name: Extract performance metrics
        if: always()
        run: |
          python scripts/extract_performance_metrics.py \
            performance-results.xml \
            performance-metrics.json
      
      - name: Upload metrics
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: performance-metrics
          path: performance-metrics.json
```

### Phase 3: 性能劣化検知（3-4時間）

#### 3.1 ベースライン設定

**ファイル**: `config/performance_baselines.json`

```json
{
  "sprint2": {
    "baseline_date": "2025-11-15",
    "thresholds": {
      "throughput_updates_per_sec": {
        "min": 100,
        "target": 416,
        "warning_threshold": 0.8
      },
      "p95_latency_ms": {
        "max": 50,
        "target": 0.3,
        "warning_threshold": 1.2
      },
      "deadlock_recovery_sec": {
        "max": 1.0,
        "target": 0.8,
        "warning_threshold": 1.2
      }
    }
  }
}
```

#### 3.2 劣化検知スクリプト

**ファイル**: `scripts/check_performance_regression.py`

```python
#!/usr/bin/env python3
"""Check for performance regression"""
import json
import sys

def check_regression(current_metrics: dict, baselines: dict) -> bool:
    """
    Returns True if regression detected, False otherwise
    """
    sprint2_baseline = baselines["sprint2"]["thresholds"]
    
    # Throughput check
    current_throughput = current_metrics["throughput_updates_per_sec"]
    min_throughput = sprint2_baseline["throughput_updates_per_sec"]["min"]
    warning_threshold = sprint2_baseline["throughput_updates_per_sec"]["warning_threshold"]
    
    if current_throughput < min_throughput * warning_threshold:
        print(f"⚠️ REGRESSION: Throughput {current_throughput} < {min_throughput * warning_threshold}")
        return True
    
    # Latency check
    current_latency = current_metrics["p95_latency_ms"]
    max_latency = sprint2_baseline["p95_latency_ms"]["max"]
    warning_threshold = sprint2_baseline["p95_latency_ms"]["warning_threshold"]
    
    if current_latency > max_latency * warning_threshold:
        print(f"⚠️ REGRESSION: P95 latency {current_latency}ms > {max_latency * warning_threshold}ms")
        return True
    
    print("✅ No performance regression detected")
    return False

if __name__ == "__main__":
    with open("performance-metrics.json") as f:
        current = json.load(f)
    with open("config/performance_baselines.json") as f:
        baselines = json.load(f)
    
    has_regression = check_regression(current, baselines)
    sys.exit(1 if has_regression else 0)
```

#### 3.3 CI ワークフローでの劣化検知

```yaml
      - name: Check for performance regression
        if: always()
        run: |
          python scripts/check_performance_regression.py
        continue-on-error: true
        id: regression_check
      
      - name: Notify Slack on regression
        if: steps.regression_check.outcome == 'failure'
        uses: slackapi/slack-github-action@v1
        with:
          webhook-url: ${{ secrets.SLACK_WEBHOOK_URL }}
          payload: |
            {
              "text": "📉 Performance regression detected in Sprint 2 tests",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*Performance Regression Detected*\n\nSprint 2 performance metrics below threshold.\n\n<${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}|View Details>"
                  }
                }
              ]
            }
```

---

## 実装スケジュール

### 推奨タイミング

**Sprint 3 Week 2 (Day 12-14)** または **Sprint 4 Week 1**

**理由**:
- Sprint 3の主要機能実装後に時間的余裕が生まれる
- Sprint 3でのリアルタイム機能が性能に影響する可能性があるため、その後の監視が重要
- 緊急性は低いが、継続的監視の価値は高い

### 実装順序

1. **Day 1 (2-3時間)**: Phase 1実装
   - GitHub Actions ワークフロー作成
   - 手動実行テスト
   - 基本動作確認

2. **Day 2 (3-4時間)**: Phase 2-3実装
   - メトリクス抽出スクリプト
   - 劣化検知スクリプト
   - ベースライン設定
   - Slack通知テスト

3. **Day 3 (1-2時間)**: ドキュメント & 検証
   - CI設定ガイド作成
   - 運用手順書作成
   - 1週間の監視期間

---

## 依存関係

### 必須

- [ ] GitHub Actions が有効化されている
- [ ] PostgreSQL 15がCI環境で利用可能
- [ ] Slack Webhook URLがシークレットに設定されている

### 推奨

- [ ] Sprint 3実装完了（性能への影響を考慮）
- [ ] TimescaleDB統合（将来的なメトリクス保存先）

---

## リスクと対策

| リスク | 確率 | 影響 | 対策 |
|--------|------|------|------|
| CI実行時間が長すぎる | Medium | Low | 並列実行、タイムアウト設定（30分） |
| False positive（誤検知） | Medium | Medium | Warning threshold を適切に設定（80%） |
| メトリクス抽出の失敗 | Low | Medium | メトリクス抽出エラー時も通知 |
| CI環境とローカルの性能差 | Medium | Medium | CI固有のベースライン設定 |

---

## 成果物

### 実装ファイル

- `.github/workflows/nightly-performance.yml`
- `scripts/extract_performance_metrics.py`
- `scripts/check_performance_regression.py`
- `config/performance_baselines.json`

### ドキュメント

- `docs/operations/nightly_ci_guide.md`（CI設定・運用ガイド）
- `docs/performance/baseline_management.md`（ベースライン管理手順）

### CI成果物（毎晩生成）

- `performance-results.xml`（JUnit形式）
- `performance-metrics.json`（メトリクス）
- Slack通知（失敗/劣化時）

---

## 参考資料

### Sprint 2関連

- Sprint 2最終完了報告書: `bridge_lite_sprint2_final_completion_report.md`
- Sprint 2仕様書: `docs/02_components/bridge_lite/architecture/bridge_lite_sprint2_spec.md`
- 性能テスト実装: `tests/performance/test_sprint2_*.py`

### CI/CD参考

- GitHub Actions Documentation: https://docs.github.com/en/actions
- pytest-benchmark: https://pytest-benchmark.readthedocs.io/
- JUnit XML format: https://llg.cubic.org/docs/junit/

---

## 関連Issue

- なし（初回Issue）

---

## チェックリスト

実装開始前:
- [ ] Sprint 2が main にマージ済み
- [ ] Sprint 3の主要機能実装が完了または目処が立っている
- [ ] GitHub Actions設定権限を確認
- [ ] Slack Webhook URL取得済み

実装完了時:
- [ ] GitHub Actions ワークフローが動作確認済み
- [ ] 手動実行で性能テストがPASS
- [ ] メトリクス抽出が正常動作
- [ ] 劣化検知ロジックが動作確認済み
- [ ] Slack通知が正常送信
- [ ] ドキュメント作成済み
- [ ] 1週間の試験運用完了

---

**作成日**: 2025-11-15  
**作成者**: Kana（外界翻訳層 / Claude Sonnet 4.5）  
**承認待ち**: 宏啓（プロジェクトオーナー）  
**実装予定**: Sprint 3 Week 2 または Sprint 4 Week 1
