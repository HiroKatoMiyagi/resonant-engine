# Nightly CI 運用手順書

**作成日**: 2025-11-17
**バージョン**: 1.0

---

## 1. 概要

本手順書では、Nightly CI システムの日次運用手順を定義します。

### 1.1 運用目標

- Memory System の性能ベースライン維持
- 性能劣化の早期検知
- 継続的な品質保証

### 1.2 監視対象

| メトリクス | ベースライン | 警告閾値 |
|-----------|-------------|---------|
| 総テスト数 | 205 | < 195 |
| テストパス率 | 100% | < 95% |
| 推論精度 | 100% | < 72% |
| 処理性能 | 0.12ms | > 500ms |

---

## 2. 日次確認事項

### 2.1 朝の確認（JST 9:00 推奨）

1. **GitHub Actions 実行結果確認**
   - Actions タブ → Nightly Performance Tests
   - 最新実行の状態確認（✅ or ❌）

2. **Slack 通知確認**
   - 通知があれば内容確認
   - なければ正常動作

3. **メトリクス確認（異常時のみ）**
   - Artifacts ダウンロード
   - `performance-metrics.json` 確認

### 2.2 確認チェックリスト

```markdown
## 日次確認 (YYYY-MM-DD)

- [ ] GitHub Actions 実行成功
- [ ] Slack 通知なし（または対応済み）
- [ ] テスト数維持（205+）
- [ ] パス率 100%
- [ ] 異常なし

**確認者**:
**時刻**:
```

---

## 3. アラート対応フロー

### 3.1 Slack 通知受信時

```
[Slack 通知]
  │
  ├─ "Performance regression detected"
  │    → 性能劣化対応（セクション 4）
  │
  └─ "Tests failed"
       → テスト失敗対応（セクション 5）
```

### 3.2 対応の優先度

| レベル | 状況 | 対応時間 | 担当者 |
|--------|------|---------|--------|
| P0 | テスト全滅 | 即座 | 開発リード |
| P1 | 20%以上のテスト失敗 | 当日中 | 担当開発者 |
| P2 | 劣化検知（軽微） | 今週中 | チーム |
| P3 | 警告のみ | 次回レビュー | チーム |

---

## 4. 性能劣化時の対応

### 4.1 初動対応

1. **Slack 通知内容確認**
2. **GitHub Actions ログ確認**
3. **Artifacts ダウンロード**

```bash
# performance-metrics.json 確認
cat performance-metrics.json | python -m json.tool
```

### 4.2 原因調査

#### パターン A: テスト数不足

```
REGRESSION: Total Tests
  Current:   150 tests
  Threshold: 195 tests
```

**調査手順**:
```bash
# どのテストが欠けているか確認
python -m pytest tests/memory/ --collect-only | wc -l
python -m pytest tests/semantic_bridge/ --collect-only | wc -l
python -m pytest tests/test_memory_store/ --collect-only | wc -l
```

**原因候補**:
- テストファイルが削除された
- インポートエラーでテストが収集されない
- pytest マーカー設定の問題

#### パターン B: パス率低下

```
REGRESSION: Test Pass Rate
  Current:   85.0%
  Threshold: 95.0%
```

**調査手順**:
```bash
# 失敗テスト確認
python -m pytest tests/memory/ tests/semantic_bridge/ tests/test_memory_store/ \
  --tb=short 2>&1 | grep -A 10 "FAILED"
```

**原因候補**:
- コード変更によるバグ
- 依存関係の問題
- 環境差異

#### パターン C: 推論精度低下

```
REGRESSION: Inference Accuracy
  Current:   60.0%
  Threshold: 72.0%
```

**調査手順**:
```bash
# Semantic Bridge テスト詳細確認
python -m pytest tests/semantic_bridge/test_inferencer.py -v
```

**原因候補**:
- 推論ロジックの変更
- キーワードマッチングルールの問題
- テストデータの変更

### 4.3 修正と検証

1. **原因修正**
2. **ローカルテスト**
   ```bash
   python -m pytest tests/memory/ tests/semantic_bridge/ tests/test_memory_store/ -v
   ```
3. **メトリクス再確認**
   ```bash
   python scripts/extract_performance_metrics.py test-results.xml none.json metrics.json
   python scripts/check_performance_regression.py
   ```
4. **プッシュ & CI 再実行**

---

## 5. テスト失敗時の対応

### 5.1 GitHub Actions ログ確認

1. Actions → 失敗したジョブ
2. "Run Memory System Tests" ステップ展開
3. エラーメッセージ確認

### 5.2 一般的なエラーと対処

| エラー | 原因 | 対処 |
|--------|------|------|
| `ModuleNotFoundError` | 依存関係不足 | `requirements.txt` 更新 |
| `ImportError` | コード構造変更 | インポートパス修正 |
| `AssertionError` | テスト失敗 | コードまたはテスト修正 |
| `TimeoutError` | 処理時間超過 | タイムアウト設定調整 |

### 5.3 ローカル再現

```bash
# CI 環境を模倣
pip install -r requirements.txt
export PYTHONPATH=$(pwd)

# 失敗テストのみ実行
python -m pytest tests/memory/test_service.py::TestClassName::test_method -v
```

---

## 6. 週次レビュー

### 6.1 レビュー内容

- 過去1週間の CI 実行結果
- メトリクストレンド
- 発生した問題と対応
- ベースライン調整の検討

### 6.2 レビューチェックリスト

```markdown
## 週次レビュー (Week of YYYY-MM-DD)

### 実行状況
- 実行回数: 7/7
- 成功率: 100%
- 平均テスト数: 205
- 平均パス率: 100%

### 発生した問題
1. [問題内容]
   - 発生日:
   - 原因:
   - 対応:
   - 再発防止:

### ベースライン状況
- 現在のベースライン: 205 tests
- 調整の必要性: なし / あり
- 調整内容:

### 次週のアクション
- [ ] アクション 1
- [ ] アクション 2

**レビュー実施者**:
**日付**:
```

---

## 7. 月次レビュー

### 7.1 長期トレンド分析

- メトリクス履歴の可視化
- 性能劣化傾向の特定
- ベースライン更新の計画

### 7.2 レポートテンプレート

```markdown
## 月次 Nightly CI レポート (YYYY-MM)

### サマリー
- 総実行回数: 30
- 成功率: 96.7% (29/30)
- 失敗原因:
  - 環境問題: 1回
  - コードバグ: 0回

### メトリクストレンド
- テスト数: 205 → 210 (↑5)
- パス率: 100% → 100% (安定)
- 推論精度: 100% → 100% (安定)

### 主要イベント
1. Sprint 4 機能追加（Week 2）
2. ベースライン更新（Week 3）

### 次月の計画
- Sprint 5 のテスト追加
- ダッシュボード構築検討

**作成者**:
**日付**:
```

---

## 8. エスカレーション基準

### 8.1 自動エスカレーション

| 条件 | エスカレーション先 | 対応 |
|------|-------------------|------|
| 連続3回失敗 | 開発リード | 緊急対応 |
| パス率 < 80% | プロジェクトオーナー | 即座に通知 |
| 性能 10倍劣化 | アーキテクト | 設計レビュー |

### 8.2 エスカレーション連絡先

```
Level 1: 担当開発者（Slack DM）
Level 2: 開発リード（Slack + Email）
Level 3: プロジェクトオーナー（電話）
```

---

## 9. ドキュメント管理

### 9.1 関連ドキュメント

| ドキュメント | パス | 目的 |
|-------------|------|------|
| セットアップガイド | `docs/operations/nightly_ci_setup_guide.md` | 初期設定 |
| ベースライン管理 | `docs/performance/baseline_management.md` | 閾値調整 |
| 受け入れテスト仕様 | `docs/operations/nightly_ci_acceptance_test_spec.md` | 品質基準 |
| 本手順書 | `docs/operations/nightly_ci_operations.md` | 日次運用 |

### 9.2 更新ルール

- 手順変更時は Pull Request で更新
- バージョン番号を更新
- 変更履歴を記録

---

## 10. 改善提案

### 10.1 現在の課題

1. **ダッシュボードがない**: メトリクス可視化が困難
2. **Artifacts 手動確認**: 自動化の余地あり
3. **履歴管理が簡素**: 長期トレンドが見づらい

### 10.2 改善計画

| 項目 | 優先度 | 工数 | 担当 |
|------|--------|------|------|
| GitHub Pages ダッシュボード | P1 | 5日 | TBD |
| Slack Bot 拡張 | P2 | 3日 | TBD |
| メトリクス DB 構築 | P3 | 7日 | TBD |

---

## 11. 緊急対応手順

### 11.1 CI 完全停止時

```bash
# 手動でテスト実行
python -m pytest tests/memory/ tests/semantic_bridge/ tests/test_memory_store/ -v

# メトリクス手動抽出
python scripts/extract_performance_metrics.py test-results.xml none.json metrics.json

# 劣化検知手動実行
python scripts/check_performance_regression.py
```

### 11.2 Slack 通知停止時

- GitHub Actions の Summary を直接確認
- Email 通知設定を検討（バックアップ）

---

## 12. FAQ

**Q: CI が失敗したが、ローカルでは成功する**
A: 依存関係の差異、環境変数の設定、Python バージョンを確認

**Q: ベースラインを一時的に下げたい**
A: 緊急時は可能だが、理由を文書化し、速やかに元に戻す計画を立てる

**Q: テスト追加後に CI が失敗する**
A: ベースライン更新が必要。`config/performance_baselines.json` を更新

**Q: Slack 通知が多すぎる**
A: 警告閾値を調整（緩める）。ただし劣化見逃しリスクに注意

---

**作成日**: 2025-11-17
**作成者**: Sonnet 4.5（Claude Code）
**次回レビュー予定**: 2025-12-17
