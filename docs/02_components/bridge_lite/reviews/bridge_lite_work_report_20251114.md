# Bridge Lite 作業報告書（2025-11-14）

## サマリー
- Bridge Lite の v2.0 仕様に沿ってコア抽象とプロバイダー層を再構築し、モジュール全体を整理しました。
- 既存利用者向けに後方互換のラッパーを維持しながら、新ファクトリ構成で環境変数ベースの切り替えを実現しています。
- Intent ライフサイクルを網羅する新テストスイートを実装し、モック構成での自動検証を追加しました。
- 外部 API キー未設定時の失敗を回避するため、テスト実行時はモックブリッジへフォールバックさせる仕組みを導入済みです。

## 実施内容
### 1. コア抽象とインターフェース更新
- `bridge/core/data_bridge.py`・`ai_bridge.py`・`feedback_bridge.py`・`audit_logger.py`
  - v2.0 仕様に基づきメソッドシグネチャを整理し、Intent の保存・処理・再評価・監査を明確に分離。
  - 型ヒントとドキュメント文字列を整備し、各ブリッジの責務を明文化。

### 2. プロバイダー層の再編成
- データ: `bridge/providers/data/{postgres_data_bridge.py, mock_data_bridge.py}` で Postgres/モックの2系統を提供。
- AI: `bridge/providers/ai/{kana_ai_bridge.py, mock_ai_bridge.py}` を新設し、Anthropic ベースの実装とモック実装を分離。
- フィードバック: `bridge/providers/feedback/{yuno_feedback_bridge.py, mock_feedback_bridge.py}` を作成し、Yuno(API) とモックを切り替え可能に。
- 監査: `bridge/providers/audit/{postgres_audit_logger.py, mock_audit_logger.py}` を定義し、Postgres ロガーとインメモリモックを実装。
- 旧構成との互換: `bridge/providers/{mock_bridge.py, postgresql_bridge.py, claude_bridge.py, yuno_feedback_bridge.py}` を更新し、新実装へのデリゲートと警告表示で互換性を維持。

### 3. BridgeFactory の刷新
- `bridge/factory/bridge_factory.py`
  - DATA/AI/FEEDBACK/AUDIT の各ブリッジを環境変数で制御できるよう再設計。
  - `postgres/postgresql/pg`、`kana/claude` 等の別名をサポートして既存インフラからの移行を容易化。
  - 未設定時はモック構成をデフォルト化し、ローカルテスト時の外部依存を削減。

### 4. テスト整備
- 既存テスト: `tests/bridge/test_mock_data_bridge.py`・`test_yuno_feedback_bridge.py`・`test_audit_logger.py` を新インターフェースへ対応。
- 新規追加: `tests/bridge/test_intent_lifecycle_suite_v1.py`
  - Intent のライフサイクル（RECEIVED→CLOSED）をシナリオベースで検証。
  - pytest-asyncio の Strict モード向けに `pytest_asyncio.fixture` を採用し、モック構成で自動的にブリッジを生成。
  - モック環境でも挙動を保証するため、例外発生がないケースへの検証ロジックを分岐。

### 5. リポジトリ衛生
- 誤って追加された関連外ドキュメントを削除し、Bridge Lite 関連ファイルのみが差分に残るよう調整。

## テスト実行
| コマンド | 対象 | 結果 |
| --- | --- | --- |
| `PYTHONPATH=. ./venv/bin/pytest tests/bridge` | 既存ブリッジ単体テスト | 5 passed |
| `PYTHONPATH=. ./venv/bin/pytest tests/bridge/test_intent_lifecycle_suite_v1.py` | Intent ライフサイクル統合テスト | 4 passed |

> 備考: Intent ライフサイクルテストは環境変数でブリッジ種別をモックに固定することで、外部 API キー未設定でも安定して実行可能です。

## 残課題・リスク
- **実運用設定の切り替え:** 本番運用では `AI_BRIDGE_TYPE=kana` などの設定と API キー登録が必須。インフラ側の環境変数設計を反映する必要があります。
- **Audit ログの永続化:** Postgres ロガーのスキーマ定義とマイグレーション手順が未整備。別途ドキュメント化と初期化スクリプトが必要です。
- **Yuno フィードバック実装:** 現状はOpenAIベースの仮実装。プロダクション仕様に合わせたAPI制約・レスポンス整形の確認が残っています。
- **互換レイヤーの廃止計画:** 旧モジュール向けのラッパーは暫定措置のため、消費側コードの移行完了時期を見極めた上で削除計画を策定する必要があります。

## 次のアクション候補
1. Audit/Postgres テーブル定義とマイグレーション手順の整備。
2. Yuno フィードバック API を実運用仕様に合わせて調整し、エンドツーエンド試験を追加。
3. Daemon プロセス側での Intent ステータス更新（CLOSED まで）を統合テストに取り込む。
4. BridgeFactory の設定値一覧を README / Ops Runbook に追記し、環境構築手順を明文化。
5. 旧ラッパーモジュールの利用箇所を洗い出して移行ロードマップを策定。

---
本報告書に関する質問や追補事項があれば、Bridge Lite 担当までお知らせください。