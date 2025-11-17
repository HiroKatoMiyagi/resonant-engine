# Alert Manager 実装計画（Sprint 3）

## 1. 仕様要約
- 出典: `docs/02_components/bridge_lite/architecture/bridge_lite_sprint3_spec.md` Section 7, `docs/sprints/bridge_lite_sprint3_start.md`（Day 14 指示）
- ゴール: Intent/Auditメトリクスを監視し、閾値超過時に Slack / Email / Webhook / Log へ通知する常駐プロセスを提供する。
- 必須要素:
  1. `AlertRule`（名前、説明、重大度、SQLベース条件、閾値、クールダウン、チャネル定義）
  2. デフォルトルール4本（高エラーレート、高コレクション率、遅延処理、無活動）
  3. `AlertManager` が `asyncpg` プールを介して一定間隔で条件を評価
  4. チャネル別ディスパッチ（Slack Webhook, Email, Generic Webhook, Log）
  5. `python -m bridge.alerts.manager` で常駐させる CLI / runner
  6. Sprint 3 Done Definition: Alert 実装 + 3テスト + ドキュメント

## 2. 現状整理（2025-11-16 時点）
- `bridge/alerts/` 配下は未作成。Alert機能に関連するコードは存在しない。
- Dashboard/Metrics/Realtime 実装は進行中で、AlertManager は次フェーズ。
- `.env` 例に `SLACK_WEBHOOK_URL` と `ALERT_WEBHOOK_URL` 変数が追加されているが、未使用。
- テストスイートにも `tests/alerts/` ディレクトリは無い。

## 3. モジュール構成案

### 3.1 `bridge/alerts/config.py`
- `AlertSeverity` / `AlertChannel` Enum を Sprint Spec に沿って定義。
- `AlertRule` dataclass（name, description, severity, condition(SQL), threshold, cooldown_minutes, channels）。
- `DEFAULT_ALERT_RULES` を 4 本登録。SQL 文は spec の条件をそのまま使用（`intent_corrections` テーブルや `audit_logs_ts` を参照）。
- Optional: チャネル別設定（Slack/Webhook URL, Email 送信設定）をここにまとめる構成も検討。

### 3.2 `bridge/alerts/manager.py`
- `AlertManager` クラスを spec の疑似コード通りに実装。
  - `__init__(database_url, rules=DEFAULT_ALERT_RULES, *, pool_factory=None, session_factory=None)`
  - `start(interval_seconds=60)` がループを開始し `_evaluate_all_rules` を呼ぶ。
  - `_evaluate_rule` が SQL 実行 → 閾値判定 → `_send_alert`。`no_activity` のみ「閾値未満で発火」ルール。
  - クールダウン管理: `self.last_alerts` に `rule.name -> datetime` を保存。
  - `_send_alert` がチャネルごとに `_send_slack`, `_send_email`, `_send_webhook`, `_log_alert` を呼び出す。
- CLI エントリポイント: `asyncio.run(AlertManager(...).start())` を `if __name__ == "__main__"` または `bridge/alerts/__main__.py` で提供。

### 3.3 `bridge/alerts/notifier.py`（任意）
- Slack や Webhook 送信処理を別モジュールに切り出すとテスト容易。
- `aiohttp.ClientSession` を抽象化して、ユニットテストでモックしやすくする。

### 3.4 `bridge/alerts/__init__.py`
- パブリック API として `AlertManager`, `AlertRule`, `AlertSeverity`, `AlertChannel`, `DEFAULT_ALERT_RULES` を再エクスポート。

### 3.5 ランナー / ライフサイクル
- CLI: `python -m bridge.alerts.manager` で常駐。
- FastAPI への統合は optional。現状は別プロセス想定だが、`bridge/api/app.py` の startup/shutdown で `AlertManager` を Task として走らせる Hook も検討（負荷・長期的には別 daemon が理想）。

## 4. データフロー
1. `AlertManager.start()` が interval（初期 60 秒）で `_evaluate_all_rules` を実行。
2. 各 `AlertRule.condition` SQL が `asyncpg` 経由で実行され、`fetchval` の結果（float or int）を取得。
3. `_check_threshold` が値と `rule.threshold` を比較し、必要に応じて `_send_alert` を発火。
4. `_send_alert` はチャネルごとに非同期送信を行い、成功したら `last_alerts[rule.name] = now` を更新。
5. Slack/Webhook 送信時は `SLACK_WEBHOOK_URL` / `ALERT_WEBHOOK_URL` 環境変数を参照、未設定時は警告ログのみ。

## 5. 実装ステップ
1. **スケルトン作成**: `bridge/alerts/` ディレクトリ、`__init__.py`, `config.py`, `manager.py`, `__main__.py` を追加。
2. **設定モジュール**: Enum/Dataclass/Default Rules を spec から移植。SQL のテーブル名 (`intents`, `intent_corrections`, `audit_logs_ts`) を再確認。
3. **AlertManager**: 
   - プール初期化／共有
   - ルール評価、クールダウン、しきい値ロジック
   - Slack/Webhook/Email/Log チャネル
   - 例外処理（`logger.error`）。
4. **ランナー**: `asyncio.run(main())` 形式で CLI 起動を実装。環境変数チェック（`DATABASE_URL` 存在確認）。
5. **テスト（tests/alerts/）**: 少なくとも 3 件
   - クールダウン判定テスト: 連続トリガーで 2 回目以降が抑制されるか。
   - 閾値判定テスト: `no_activity`（逆しきい値）と通常ルールの両方を検証。
   - 通知チャネルテスト: Slack/Webhook 送信で正しい payload が作られるか（`aiohttp` をモック）。
6. **ドキュメント**: 本計画書に加え、README / 運用ガイドへ AlertManager 起動手順を追記予定。

## 6. テスト計画（詳細）
| テスト名 | 目的 | 手法 |
| --- | --- | --- |
| `test_alert_manager_triggers_when_threshold_exceeded` | SQL 結果 > threshold で `_send_alert` が呼ばれる | モックプールで固定値返却、`AsyncMock` で `_send_alert` を検証 |
| `test_alert_manager_respects_cooldown_and_no_activity_rule` | `no_activity` の逆比較と cooldown を確認 | 疑似 `last_alerts` を設定して `_evaluate_rule` を実行 |
| `test_slack_notifier_builds_expected_payload` | Slack Webhook への JSON 形式を保証 | `aiohttp.ClientSession` をモックし、payload を検証 |

## 7. リスクと確認事項
- **TimescaleDB 依存**: `slow_processing` ルールは `audit_logs_ts` テーブルを前提としている。まだ実装されていない場合は feature flag でスキップする必要がある。
- **Email チャネル**: 仕様では `pass` 扱い。MVP では LOG/Slack/Webhook のみ対応し、メールは NotImplemented ログにする案。
- **常駐タスクの配置**: FastAPI 内でタスクを動かすと uvicorn 停止時の後片付けが必要。現状は別スクリプト起動で進め、Sprint 4 で本番オーケストレーションに組み込む。
- **環境変数未設定**: Slack/Webhook URL が空の場合、起動時に WARNING を出し fallback を文書化する。

---
この計画に沿って Alert Manager 実装を進めれば、Sprint 3 Done Definition の残タスク（Alert 機能 + テスト）に着手可能な状態となる。
