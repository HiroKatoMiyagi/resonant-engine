# Bridge Lite Sprint 2 — Concurrency Notes (Day 6-7)

本ドキュメントは Sprint 2 Day 6-7 の成果物として、ロック戦略の意思決定、実装済みベストプラクティス、および Re-eval API を中心としたコンカレンシー注意事項を集約したものです。最新コードベース (`main` branch, 2025-11-15) と pytest スイートを唯一の根拠として記述しています。

---

## 1. Lock Strategy Decisions

| 対象オペレーション | 適用戦略 | 実装箇所 | 根拠となるテスト | 補足 |
| --- | --- | --- | --- | --- |
| ステータス更新 (`update_intent_status`) | Pessimistic | `bridge/providers/data/mock_data_bridge.py` の `lock_intent_for_update` 再入保護／ステータス検証 | `tests/performance/test_sprint2_performance.py::test_status_update_throughput_meets_target` | RE-LOCK を避けるため `self._active_sessions` でタスク所有権を追跡。許容遷移は `IntentModel._ALLOWED_STATUS_TRANSITIONS` に従う。 |
| Pipeline 実行 (`BridgeSet.execute_with_lock`) | Pessimistic (fallback で optimistic) | `bridge/core/bridge_set.py` | `tests/concurrency/test_sprint2_concurrent_updates.py::test_bridge_set_execute_with_lock_serializes_pipeline` | 未永続 Intent は optimistic 経路で実行し、永続済み Intent には悲観ロック＋ `retry_on_deadlock` で再試行。 |
| Re-eval API (`reeval_intent`) | Optimistic + バックオフ | `bridge/api/reeval.py` & `bridge/core/concurrency.py` | `tests/performance/test_sprint2_performance.py::test_reeval_latency_under_contention`、`tests/concurrency/test_sprint2_concurrent_updates.py::test_concurrent_reeval_retries_until_success` | `update_intent_if_version_matches` によるバージョン一致を必須化し、MAX_RETRIES=3・指数バックオフ(0.1s base + jitter)で衝突を解消。 |
| Correction履歴永続化 (`save_correction`) | Optimistic (同一 correction_id でガード) | `bridge/providers/data/mock_data_bridge.py::save_correction` | `tests/concurrency/test_sprint2_concurrent_updates.py::test_concurrent_reeval_retries_until_success` | `correction_id` 重複時は no-op とし、意図的にロックを取得しない。 |
| Lock 取得 API (`lock_intent_for_update`) | Pessimistic + Timeout | `bridge/providers/data/mock_data_bridge.py` | `tests/performance/test_sprint2_performance.py::test_lock_acquisition_p95_latency`、`tests/concurrency/test_sprint2_concurrent_updates.py::test_lock_timeout_when_lock_held` | 1 Intent = 1 asyncio.Lock を保持し、Timeout(デフォルト 5s) で `LockTimeoutError` を発火。 |

---

## 2. Concurrency Best Practices Guide

1. **Intent を書き換える前に必ず `IntentModel.validate_status_transition` を通過させること。** これにより `INVALID_STATUS` が API レイヤで早期検出される。
2. **Pipeline 実行は `BridgeSet.execute_with_lock` 経由が既定。** 直接 `_execute_pipeline` を呼ぶ場合は「永続済み Intent ではない」「競合が発生しない」ことを明示せよ。
3. **Re-eval 呼び出しは idempotent diff を前提とし、`reason` と `source` を必ず埋める。** `reeval_intent` は (intent_id + diff) をハッシュ化して再適用を防ぐ。
4. **Lock を取得したセッションでは再入処理が有効** (`MockDataBridge` の `_active_sessions`)。同一タスク内で `update_intent_status` を呼ぶときは再度 `lock_intent_for_update` を呼ばないこと。
5. **性能回帰の検知**: Day 6 で追加した `tests/performance/test_sprint2_performance.py` を CI の nightly スイートに登録し、100 updates/sec・平均 Re-eval < 200ms・Lock P95 < 50ms を継続監視する。
6. **Deadlock/Timeout が発生した場合**: `bridge.core.retry.retry_on_deadlock` と `LockTimeoutError` を捕捉し、`ConcurrencyConfig` の閾値を先に点検。値変更は専用 PR で追跡すること。

---

## 3. API Concurrency Notes (Re-eval Endpoint)

| 項目 | 内容 |
| --- | --- |
| エンドポイント | `POST /api/v1/intent/reeval` (`bridge/api/reeval.py`) |
| ロック戦略 | Optimistic (`update_intent_if_version_matches`) + MAX_RETRIES=3 / backoff base 100ms / jitter 50ms |
| 競合時のレスポンス | `409 CONCURRENCY_CONFLICT` または `409 INVALID_STATUS` (意図が完了・失敗済のとき) |
| Idempotency | `intent.apply_correction` が (intent_id + diff) 派生の `correction_id` を生成。既存の場合 `already_applied: true` を返し副作用なし。 |
| 許可 Actor | `PhilosophicalActor.YUNO` / `PhilosophicalActor.KANA` のみ。TSUMU など他アクターは `403 INVALID_SOURCE`. |
| メトリクス/ログ | `AuditEventType.REEVALUATED` に `already_applied` と `correction_id` を添付。Prometheus 連携時は `bridge_version_conflicts_total` を参照。 |

**API利用者向け推奨**
- 高頻度で Re-eval を叩く場合は 50 リクエスト単位でバッチ化し、アプリ側で指数バックオフを併用する。
- Re-eval の diff には必ず `payload` 直下に限定的な変更を含め、空 diff は送らない (validation error になる)。
- 409 応答を受け取った場合は「Intent が COMPLETED/FAILED か」をまず GET で確認し、再評価が無意味であれば即中断する。

---

## 4. Performance Validation Snapshot (2025-11-15)

| テスト | 目的 | 結果 |
| --- | --- | --- |
| `test_status_update_throughput_meets_target` | 200 Intent を 25 並列で更新し、100 updates/sec 達成を担保 | 0.48s (≈416 updates/sec) PASS |
| `test_reeval_latency_under_contention` | 単一 Intent へ 50 Re-eval を同時投入し、平均 < 200ms を保証 | 平均 9.6ms PASS |
| `test_lock_acquisition_p95_latency` | 100 Intent のロック取得 P95 < 50ms | P95 ≈ 0.3ms PASS |

※ 実測値はローカル Apple Silicon (Python 3.14) での pytest 実行ログから取得。CI でも同テストを `-m "not slow"` の対象外として別ジョブに配置することを推奨。

---

## 5. Review & Follow-up

1. **Kana Review パッケージ**: 本ドキュメント + `tests/performance/test_sprint2_performance.py` + `pytest.ini` の diff を提出。レビュー観点は「閾値の根拠」「Re-eval API 仕様反映」「Lock戦略の整合性」。
2. **フィードバック対応プロトコル**: Kana コメントは `docs/reports/work_report_20251115_sprint2_concurrency.md` に反映し、必要があれば `ConcurrencyConfig` を更新後に本ドキュメントへ追記する。
3. **リリース判定**: スプリント完了条件 (Throughput>=100 / P95 lock<50ms / Re-eval <200ms) を満たしたため、Day 7 ステージング移行前の性能ゲートをクリア済み。残タスクはレビュー承認とメトリクス配線のみ。

---

以上により、Day 6 の性能検証と Day 7 のドキュメント要件を満たすための情報は揃いました。レビュー後の差分も本ファイルで一元管理します。
