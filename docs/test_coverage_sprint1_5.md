# Sprint 1.5 Coverage Report

**計測日**: 2025-11-15

## 実行コマンド

```bash
PYTHONPATH=. venv/bin/pytest \
  tests/bridge/test_sprint1_5_factory.py \
  tests/bridge/test_sprint1_5_yuno_feedback_bridge.py \
  tests/bridge/test_sprint1_5_bridge_set.py \
  tests/integration/test_sprint1_5_feedback_reeval_integration.py \
  --cov=bridge.core.reeval_client \
  --cov=bridge.providers.feedback.yuno_feedback_bridge \
  --cov=bridge.providers.feedback.mock_feedback_bridge \
  --cov=bridge.factory.bridge_factory \
  --cov-report=term-missing \
  --cov-report=html:coverage_report_sprint1_5
```

## 集計結果

| モジュール | ステートメント | 未カバー | カバレッジ | 備考 |
|------------|----------------|----------|------------|------|
| `bridge.core.reeval_client` | 17 | 0 | **100%** | 主要フロー・例外すべて網羅 |
| `bridge.factory.bridge_factory` | 58 | 8 | **86%** | 例外パス（設定不足時のフォールバック）が未実行。別環境依存のため除外。 |
| `bridge.providers.feedback.mock_feedback_bridge` | 33 | 5 | **85%** | フォールバック履歴書き込み (例外系) 未カバー。低リスクのため現状維持。 |
| `bridge.providers.feedback.yuno_feedback_bridge` | 119 | 16 | **87%** | OpenAIレスポンス整形・冪等確認の主要分岐を網羅。API障害時の深い再試行ロジックは実運用依存のため除外。 |
| **合計** | 227 | 29 | **87%** | Done Definition の 80% 基準を超過。 |

## 未カバー行の考察

- `bridge.factory.bridge_factory`: 実運用でのみ発生する例外（環境変数未設定や外部依存のロード失敗）をテストで再現すると他モジュールへ副作用が及ぶため、現段階では除外。
- `bridge.providers.feedback.mock_feedback_bridge`: ダミー環境でのエラー通知・履歴整形の分岐。モック利用では到達しないため、将来の堅牢化テストで別途検討。

## 追加メモ

- HTMLレポートは `coverage_report_sprint1_5/index.html` に出力済み。ブラウザで詳細を確認可能。
- テスト実行中に `CorrectionRecord` シリアライズに関する Pydantic 警告が 1 件発生するが、これは既知の仕様であり今回の作業範囲外とする。
