# Re-evaluation API ガイド

最終更新日: 2025-11-15

## 概要
Bridge Lite の Re-evaluation API はフィードバックループと自動補正を担うエンドポイントです。Intent が FeedbackBridge（Yuno / Mock）によって「修正が必要」と判定された際、差分 (`diff`) を適用して Intent を更新し、`correction_history` を蓄積します。

- エンドポイント: `POST /api/v1/intent/reeval`
- 認可: `source` は `YUNO` または `KANA` のみ許可
- 冪等性: `intent_id` と `diff` の組合せで一意に判定

## クイックスタート

```bash
curl -X POST http://localhost:8000/api/v1/intent/reeval \
  -H "Content-Type: application/json" \
  -d '{
    "intent_id": "550e8400-e29b-41d4-a716-446655440000",
    "source": "YUNO",
    "reason": "Automated feedback correction",
    "diff": {
      "payload": {
        "feedback.yuno.reason": "Add missing tests",
        "feedback.yuno.recommended_changes": [
          {"description": "Cover feedback diff pipeline", "priority": "high"}
        ],
        "status": "corrected"
      }
    }
  }'
```

成功時は以下のようなレスポンスが返ります。

```json
{
  "intent_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "corrected",
  "already_applied": false,
  "correction_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "applied_at": "2025-11-15T12:34:56.789Z",
  "correction_count": 2
}
```

## FeedbackBridge との統合
1. Intent が BridgeSet パイプライン（INPUT → AI → FEEDBACK → OUTPUT）を通過
2. YunoFeedbackBridge / MockFeedbackBridge が Intent を評価
3. `status` が `requires_changes` の場合、フィードバック結果から `diff` とメタデータを生成
4. ReEvalClient 経由で本 API を呼び出し
5. Intent が更新され、`correction_history` に追記
6. AuditLogger に REEVALUATED イベントが記録され、Intent ステータスは `CORRECTED` へ遷移

## Diff 形式ルール
- キーはドット区切りでネストを表現: `payload.feedback.yuno.reason`
- 値は絶対値で指定（"+5" のような演算指定は禁止）
- `payload` 以外のトップレベルも更新可能 (`metadata.*`, `status` など)
- 例: 有効な diff
  ```json
  {
    "payload": {
      "feedback.yuno.latest": {"judgment": "requires_changes"},
      "feedback.yuno.reason": "Improve coverage"
    },
    "status": "corrected"
  }
  ```
- 無効な diff の例
  ```json
  {
    "payload": {
      "metrics.coverage": "+5"  // 相対指定は禁止
    }
  }
  ```

## 冪等性の仕組み
- `intent_id` と `diff` を連結した SHA256 ハッシュで重複を判定
- 既に適用済みの場合は 200 OK で `{"already_applied": true}` を返却し、Intent は変更されません
- `correction_history` に重複レコードは追加されません

## 認可ルール
| source | 許可 | 備考 |
|--------|------|------|
| `YUNO` | ✅ | YunoFeedbackBridge（GPT統合） |
| `KANA` | ✅ | 手動・別AIによる補正 |
| `TSUMU` | ❌ | 自己修正は無効 |

## エラーハンドリング
| ステータス | エラーコード | 説明 |
|-------------|--------------|------|
| 400 | `INVALID_DIFF` / `APPLY_FAILED` | diff の検証失敗、または Intent への適用失敗 |
| 403 | `INVALID_SOURCE` | `source` が許可リスト外 |
| 404 | `INTENT_NOT_FOUND` | 指定 Intent が未登録 |
| 409 | `INVALID_STATUS` | Intent が差分適用不可能な状態 |

詳細なレスポンス構造は Swagger UI (`/docs`) で参照できます。

## ベストプラクティス
- フィードバック側で生成する diff はミニマルに保つ（既存フィールドの全置換を避ける）
- `metadata` に `evaluation`, `recommended_changes`, `provider` などの情報を残し、監査ログと整合を取る
- API 呼び出しに失敗した場合は `reason` とステータスを FeedbackBridge のログに残す
- 大量適用時には idempotency を活用し、同じ diff を再送しても安全に保つ
- ステージング環境で Swagger UI を使い、`try it out` で diff の挙動を検証する
