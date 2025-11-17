# Nightly CI ベースライン管理手順書

**作成日**: 2025-11-17
**バージョン**: 1.0

---

## 1. 概要

本手順書では、Memory System の性能ベースラインの管理方法を定義します。

### 1.1 現在のベースライン

| コンポーネント | Sprint | テスト数 | 性能指標 | 基準日 |
|--------------|--------|---------|---------|--------|
| Memory Management | 1 | 72 | 実行時間 0.36s | 2025-11-17 |
| Semantic Bridge | 2 | 97 | 0.12ms/event, 推論精度 100% | 2025-11-17 |
| Memory Store | 3 | 36 | - | 2025-11-17 |
| **合計** | - | **205** | - | - |

### 1.2 ベースラインファイル

```
config/performance_baselines.json
```

---

## 2. ベースライン更新タイミング

### 2.1 更新すべき状況

| 状況 | 理由 | 更新内容 |
|------|------|---------|
| 新機能追加 | テスト数増加 | `min` 値を上げる |
| 意図的な性能変更 | トレードオフ判断 | `target` 値を調整 |
| 技術的負債解消 | 性能改善 | `target` 値を上げる |
| アーキテクチャ変更 | 性能特性変化 | 全体的に再評価 |

### 2.2 更新すべきでない状況

| 状況 | 理由 | 対応 |
|------|------|------|
| 一時的なテスト失敗 | 環境問題 | 原因調査・修正 |
| 偶発的な性能劣化 | バグ | 劣化原因を修正 |
| CI 環境の問題 | インフラ問題 | インフラ修正 |

---

## 3. ベースライン更新手順

### 3.1 手順概要

```
1. 変更理由の文書化
2. 新ベースライン値の決定
3. config/performance_baselines.json 更新
4. CI テストで検証
5. レビュー・承認
6. コミット・プッシュ
7. 変更履歴記録
```

### 3.2 詳細手順

#### Step 1: 変更理由の文書化

```markdown
## ベースライン更新申請

**日付**: YYYY-MM-DD
**申請者**:
**理由**: [新機能追加 / 性能改善 / アーキテクチャ変更]
**影響範囲**: [Memory Management / Semantic Bridge / Memory Store]

### 変更内容
- 旧値: XXX
- 新値: YYY
- 根拠: [Sprint完了報告書リンク / 性能テスト結果]

### リスク評価
- 変更による副作用:
- 回帰リスク:
```

#### Step 2: 新ベースライン値の決定

```bash
# 現在のテスト状況確認
PYTHONPATH=/path/to/resonant-engine python -m pytest \
  tests/memory/ tests/semantic_bridge/ tests/test_memory_store/ -v \
  | tail -10

# 出力例:
# ======================== 220 passed, X warnings in 0.58s =========================
#                          ↑新しいベースライン
```

#### Step 3: 設定ファイル更新

```bash
# バックアップ作成
cp config/performance_baselines.json config/performance_baselines.json.bak

# 編集
vim config/performance_baselines.json
```

更新例（テスト追加時）：

```json
{
  "memory_system": {
    "baseline_date": "2025-12-01",  // 更新日
    "components": {
      "memory_management": {
        "tests": 85  // 72 → 85
      },
      "semantic_bridge": {
        "tests": 110  // 97 → 110
      },
      "memory_store": {
        "tests": 45  // 36 → 45
      }
    },
    "thresholds": {
      "total_tests": {
        "min": 240,  // 205 → 240
        "target": 240
      }
    }
  }
}
```

#### Step 4: CI テスト検証

```bash
# ベースライン整合性テスト
PYTHONPATH=/path/to/resonant-engine python -m pytest tests/ci/ -v

# 期待結果: 全テストパス（特に以下）
# test_baseline_values_match_sprint_reports
# test_total_test_count_baseline
```

**注意**: テスト自体も更新が必要な場合あり：

```python
# tests/ci/test_nightly_workflow.py
def test_baseline_values_match_sprint_reports(self):
    # 新しい値に合わせて更新
    assert components['memory_management']['tests'] == 85  # 72 → 85
```

#### Step 5: レビュー・承認

- Pull Request 作成
- チームレビュー
- 承認取得

#### Step 6: コミット・プッシュ

```bash
git add config/performance_baselines.json
git add tests/ci/test_nightly_workflow.py  # 必要に応じて
git commit -m "chore: update performance baselines for Sprint X

- Memory Management: 72 → 85 tests
- Semantic Bridge: 97 → 110 tests
- Memory Store: 36 → 45 tests
- Total: 205 → 240 tests

Reason: New features added in Sprint X"

git push origin feature-branch
```

#### Step 7: 変更履歴記録

本ドキュメント末尾の「変更履歴」セクションに記録。

---

## 4. 閾値（Threshold）調整

### 4.1 警告閾値の意味

```json
"total_tests": {
  "min": 205,           // 最低テスト数
  "target": 205,        // 目標テスト数
  "warning_threshold": 0.95  // min の 95% 未満で警告
}
```

計算例：
- `min = 205`
- `warning_threshold = 0.95`
- 警告発生: `current < 205 * 0.95 = 194.75` → 194以下で警告

### 4.2 閾値調整の考慮事項

| 項目 | 緩い閾値 | 厳しい閾値 |
|------|---------|-----------|
| 例 | 0.80 (80%) | 0.98 (98%) |
| 利点 | 誤検知少ない | 早期検知 |
| 欠点 | 劣化見逃し | 誤検知多い |
| 推奨状況 | 初期導入時 | 安定運用時 |

### 4.3 推奨閾値

| メトリクス | 推奨閾値 | 理由 |
|-----------|---------|------|
| total_tests | 0.95 | テスト削除は稀 |
| test_pass_rate | 0.95 | 厳しめに監視 |
| inference_accuracy | 0.90 | 推論精度は重要 |
| processing_performance_ms | 10.0 | 環境差を考慮（緩め） |

---

## 5. 特殊なケース

### 5.1 意図的な性能劣化（トレードオフ）

**状況**: 新機能追加により処理性能が低下

**対応手順**:

1. トレードオフの文書化
2. 性能劣化の許容範囲決定
3. ベースライン更新（性能目標を下げる）
4. 監視閾値の調整

```json
// 例: 処理性能を 0.12ms → 0.5ms に緩和
"processing_performance_ms": {
  "max": 50.0,
  "target": 0.5,  // 0.12 → 0.5
  "warning_threshold": 10.0,
  "comment": "Feature X追加により処理時間増加を許容（2025-12-01）"
}
```

### 5.2 テスト削除

**状況**: 古いテストを削除、新しいテストに置き換え

**対応**:
- テスト数が同等以上なら問題なし
- 減少する場合は理由を文書化

```bash
# テスト数確認
python -m pytest tests/ --collect-only | grep "test session starts"
```

### 5.3 モジュール分割

**状況**: `semantic_bridge` が2つのモジュールに分割

**対応**:
1. 新モジュール用のベースラインを追加
2. 合計テスト数を維持
3. 監視スクリプトの更新

---

## 6. 監視とアラート

### 6.1 劣化検知時の対応フロー

```
1. Slack 通知受信
2. GitHub Actions ログ確認
3. performance-metrics.json 確認
4. 原因特定
   ├─ コード変更による劣化 → 修正 or トレードオフ判断
   ├─ テスト追加漏れ → テスト追加
   └─ CI 環境問題 → インフラ修正
5. 対応実施
6. 再実行確認
```

### 6.2 誤検知対応

**状況**: 環境問題で一時的に閾値を下回る

**対応**:
- 手動で再実行
- 問題が解消されれば OK
- 繰り返す場合は閾値調整を検討

---

## 7. ベースライン履歴管理

### 7.1 変更履歴テンプレート

```markdown
## 変更履歴

### Version X.X (YYYY-MM-DD)

**変更者**:
**理由**:

| コンポーネント | 旧値 | 新値 | 変更理由 |
|--------------|------|------|---------|
| Memory Management Tests | 72 | 85 | Sprint 4 新機能 |
| Total Tests | 205 | 240 | 新機能追加 |

**関連PR**: #XXX
**関連Issue**: #YYY
```

### 7.2 現在の変更履歴

#### Version 1.0 (2025-11-17)

**変更者**: Sonnet 4.5（Claude Code）
**理由**: 初期ベースライン設定

| コンポーネント | 値 | 根拠 |
|--------------|-----|------|
| Memory Management Tests | 72 | Sprint 1 完了報告書 |
| Semantic Bridge Tests | 97 | Sprint 2 完了報告書 |
| Memory Store Tests | 36 | Sprint 3 受け入れテスト仕様書 |
| Total Tests | 205 | 上記合計 |
| Inference Accuracy | 100% | Semantic Bridge 報告書 |
| Processing Performance | 0.12ms | Semantic Bridge 報告書 |

---

## 8. 自動化の検討

### 8.1 将来の自動化案

- **自動ベースライン提案**: テスト追加時に自動的に新ベースラインを提案
- **段階的閾値調整**: 安定度に応じて閾値を自動調整
- **履歴可視化ダッシュボード**: メトリクストレンドのグラフ化

### 8.2 実装優先度

| 機能 | 優先度 | 工数見積 |
|------|--------|---------|
| 自動提案 | P2 | 2日 |
| 段階的調整 | P3 | 3日 |
| ダッシュボード | P1 | 5日 |

---

## 9. 付録

### 9.1 ベースライン設定スキーマ

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "memory_system": {
      "type": "object",
      "properties": {
        "baseline_date": { "type": "string", "format": "date" },
        "description": { "type": "string" },
        "components": { "type": "object" },
        "thresholds": { "type": "object" }
      },
      "required": ["baseline_date", "components", "thresholds"]
    }
  }
}
```

### 9.2 閾値計算ツール

```python
# 閾値計算スクリプト
def calculate_warning_threshold(min_value, warning_threshold):
    """警告が発生する境界値を計算"""
    return min_value * warning_threshold

# 使用例
total_tests_min = 205
warning_threshold = 0.95
boundary = calculate_warning_threshold(total_tests_min, warning_threshold)
print(f"Warning at: < {boundary} tests")  # < 194.75 tests
```

---

**作成日**: 2025-11-17
**作成者**: Sonnet 4.5（Claude Code）
**次回レビュー予定**: 2025-12-17
