# Backend API 高度機能統合 受け入れテスト仕様書

## 0. テスト概要

**目的**: Backend API統合が正しく完了し、WebUIから全機能が利用可能であることを確認する

**スコープ**: 
- 統合された5つの高度機能のAPI動作確認
- エンドポイントレスポンス検証
- エラーハンドリング確認
- パフォーマンス検証

**前提条件**:
- Docker環境が起動している
- PostgreSQLが稼働している
- Backend APIが起動している

---

## 1. Tier 1テスト（必須）

### Test 1.1: Contradiction Detection - 未解決矛盾取得

**目的**: プレースホルダーが削除され、実際のデータを返すことを確認

**前提条件**:
- データベースに矛盾データが存在する（テストデータ投入済み）

**実行手順**:
```bash
curl -X GET 'http://localhost:8000/api/v1/contradiction/pending?user_id=test_user' \
  -H 'Content-Type: application/json'
```

**期待される結果**:
```json
{
  "contradictions": [
    {
      "id": "uuid-xxx",
      "user_id": "test_user",
      "new_intent_id": "uuid-yyy",
      "new_intent_content": "...",
      "contradiction_type": "tech_stack",
      "confidence_score": 0.85,
      "resolution_status": "pending"
    }
  ],
  "count": 1
}
```

**検証項目**:
- [ ] HTTPステータス: 200 OK
- [ ] `contradictions`が配列である
- [ ] `count`が正の整数である
- [ ] ❌ `count`が常に0ではない（プレースホルダーではない証明）

---

### Test 1.2: Contradiction Detection - Intent矛盾チェック

**目的**: 新しいIntentの矛盾チェックが動作することを確認

**実行手順**:
```bash
curl -X POST 'http://localhost:8000/api/v1/contradiction/check' \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": "test_user",
    "intent_id": "new-intent-001",
    "intent_content": "SQLiteに変更する"
  }'
```

**期待される結果**:
```json
{
  "contradictions": [
    {
      "contradiction_type": "tech_stack",
      "confidence_score": 0.9,
      "details": {
        "previous_decision": "PostgreSQL選定",
        "conflict": "データベース変更"
      }
    }
  ],
  "count": 1
}
```

**検証項目**:
- [ ] HTTPステータス: 200 OK
- [ ] 矛盾が検出される（過去の決定と矛盾する場合）
- [ ] `contradiction_type`が正しい値である

---

### Test 1.3: Contradiction Detection - 矛盾解決

**目的**: 矛盾解決機能が動作することを確認

**前提条件**:
- Test 1.1で取得した矛盾IDを使用

**実行手順**:
```bash
curl -X PUT 'http://localhost:8000/api/v1/contradiction/{contradiction_id}/resolve' \
  -H 'Content-Type: application/json' \
  -d '{
    "resolution_action": "policy_change",
    "resolution_rationale": "要件変更により方針転換が必要",
    "resolved_by": "test_user"
  }'
```

**期待される結果**:
```json
{
  "status": "resolved",
  "contradiction_id": "uuid-xxx",
  "resolution_action": "policy_change"
}
```

**検証項目**:
- [ ] HTTPステータス: 200 OK
- [ ] `status`が"resolved"である
- [ ] データベースで矛盾のステータスが更新されている

---

### Test 1.4: Re-evaluation - Intent再評価

**目的**: Re-evaluation APIが動作することを確認

**前提条件**:
- 既存のIntentが存在する

**実行手順**:
```bash
curl -X POST 'http://localhost:8000/api/v1/intent/reeval' \
  -H 'Content-Type: application/json' \
  -d '{
    "intent_id": "existing-intent-001",
    "diff": {"priority": 10},
    "source": "YUNO",
    "reason": "優先度を上げる必要がある"
  }'
```

**期待される結果**:
```json
{
  "intent_id": "existing-intent-001",
  "status": "re-evaluated",
  "result": {
    "applied": true,
    "correction_count": 1
  }
}
```

**検証項目**:
- [ ] HTTPステータス: 200 OK
- [ ] `status`が"re-evaluated"である
- [ ] Intentが更新されている

---

### Test 1.5: Choice Preservation - 未決定選択肢取得

**目的**: 未決定の選択肢が取得できることを確認

**実行手順**:
```bash
curl -X GET 'http://localhost:8000/api/v1/memory/choice-points/pending?user_id=test_user' \
  -H 'Content-Type: application/json'
```

**期待される結果**:
```json
{
  "choice_points": [
    {
      "id": "uuid-xxx",
      "question": "データベース選定",
      "choices": [
        {"choice_id": "A", "choice_text": "PostgreSQL"},
        {"choice_id": "B", "choice_text": "SQLite"}
      ],
      "selected_choice_id": null
    }
  ],
  "count": 1
}
```

**検証項目**:
- [ ] HTTPステータス: 200 OK
- [ ] `choice_points`が配列である
- [ ] `selected_choice_id`がnullである（未決定）

---

### Test 1.6: Choice Preservation - 選択肢作成

**目的**: 新しい選択肢が作成できることを確認

**実行手順**:
```bash
curl -X POST 'http://localhost:8000/api/v1/memory/choice-points/' \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": "test_user",
    "question": "認証方式選定",
    "choices": [
      {"choice_id": "A", "choice_text": "JWT"},
      {"choice_id": "B", "choice_text": "Session"}
    ],
    "tags": ["security", "authentication"],
    "context_type": "architecture"
  }'
```

**期待される結果**:
```json
{
  "choice_point": {
    "id": "uuid-new",
    "question": "認証方式選定",
    "choices": [...],
    "tags": ["security", "authentication"],
    "created_at": "2025-11-30T..."
  }
}
```

**検証項目**:
- [ ] HTTPステータス: 200 OK
- [ ] `choice_point.id`が生成されている
- [ ] `tags`が保存されている

---

### Test 1.7: Choice Preservation - 選択決定（却下理由付き）

**目的**: 選択決定と却下理由の保存が動作することを確認

**前提条件**:
- Test 1.6で作成した選択肢IDを使用

**実行手順**:
```bash
curl -X PUT 'http://localhost:8000/api/v1/memory/choice-points/{choice_point_id}/decide' \
  -H 'Content-Type: application/json' \
  -d '{
    "selected_choice_id": "A",
    "decision_rationale": "スケーラビリティと標準化を考慮",
    "rejection_reasons": {
      "B": "セッション管理の複雑さとスケーラビリティ限界"
    }
  }'
```

**期待される結果**:
```json
{
  "choice_point": {
    "selected_choice_id": "A",
    "decision_rationale": "スケーラビリティと標準化を考慮",
    "choices": [
      {
        "choice_id": "A",
        "selected": true,
        "rejection_reason": null
      },
      {
        "choice_id": "B",
        "selected": false,
        "rejection_reason": "セッション管理の複雑さとスケーラビリティ限界"
      }
    ],
    "decided_at": "2025-11-30T..."
  }
}
```

**検証項目**:
- [ ] HTTPステータス: 200 OK
- [ ] `selected_choice_id`が"A"である
- [ ] 選択肢Bの`rejection_reason`が保存されている
- [ ] `decided_at`がnullでない

---

### Test 1.8: Choice Preservation - 検索（タグフィルタ）

**目的**: タグベース検索が動作することを確認

**実行手順**:
```bash
curl -X GET 'http://localhost:8000/api/v1/memory/choice-points/search?user_id=test_user&tags=security,authentication&limit=10' \
  -H 'Content-Type: application/json'
```

**期待される結果**:
```json
{
  "results": [
    {
      "question": "認証方式選定",
      "tags": ["security", "authentication"],
      "selected_choice_text": "JWT"
    }
  ],
  "count": 1
}
```

**検証項目**:
- [ ] HTTPステータス: 200 OK
- [ ] タグが一致する選択肢のみが返る
- [ ] `count`が正しい

---

### Test 1.9: Memory Lifecycle - ステータス取得

**目的**: メモリ使用状況が取得できることを確認

**実行手順**:
```bash
curl -X GET 'http://localhost:8000/api/v1/memory/lifecycle/status?user_id=test_user' \
  -H 'Content-Type: application/json'
```

**期待される結果**:
```json
{
  "user_id": "test_user",
  "total_memories": 150,
  "working_memory_count": 20,
  "longterm_memory_count": 130,
  "capacity_used_percentage": 0.75,
  "compression_recommended": false
}
```

**検証項目**:
- [ ] HTTPステータス: 200 OK
- [ ] `total_memories`が正の整数である
- [ ] `capacity_used_percentage`が0-1の範囲である

---

### Test 1.10: Dashboard Analytics - システム概要

**目的**: ダッシュボード概要が取得できることを確認

**実行手順**:
```bash
curl -X GET 'http://localhost:8000/api/v1/dashboard/overview' \
  -H 'Content-Type: application/json'
```

**期待される結果**:
```json
{
  "messages_count": 22,
  "intents_count": 15,
  "active_sessions": 3,
  "contradictions_pending": 2,
  "crisis_index": 45,
  "last_updated": "2025-11-30T..."
}
```

**検証項目**:
- [ ] HTTPステータス: 200 OK
- [ ] 全フィールドが存在する
- [ ] `crisis_index`が0-100の範囲である

---

## 2. Tier 2テスト（品質）

### Test 2.1: パフォーマンス - 矛盾検出

**目的**: 矛盾検出が2秒以内に完了することを確認

**実行手順**:
```bash
time curl -X POST 'http://localhost:8000/api/v1/contradiction/check' \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": "test_user",
    "intent_id": "perf-test-001",
    "intent_content": "パフォーマンステスト"
  }'
```

**期待される結果**:
- レスポンス時間 < 2秒

**検証項目**:
- [ ] レスポンスタイム < 2秒

---

### Test 2.2: パフォーマンス - 選択肢検索

**目的**: 選択肢検索が500ms以内に完了することを確認

**実行手順**:
```bash
time curl -X GET 'http://localhost:8000/api/v1/memory/choice-points/search?user_id=test_user&limit=100' \
  -H 'Content-Type: application/json'
```

**期待される結果**:
- レスポンス時間 < 500ms

**検証項目**:
- [ ] レスポンスタイム < 500ms

---

### Test 2.3: エラーハンドリング - 無効なユーザーID

**目的**: 無効なユーザーIDで適切なエラーが返ることを確認

**実行手順**:
```bash
curl -X GET 'http://localhost:8000/api/v1/contradiction/pending?user_id=' \
  -H 'Content-Type: application/json'
```

**期待される結果**:
```json
{
  "detail": [
    {
      "loc": ["query", "user_id"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**検証項目**:
- [ ] HTTPステータス: 422 Unprocessable Entity
- [ ] エラーメッセージが明確である

---

### Test 2.4: エラーハンドリング - 存在しない矛盾ID

**目的**: 存在しない矛盾IDで適切なエラーが返ることを確認

**実行手順**:
```bash
curl -X PUT 'http://localhost:8000/api/v1/contradiction/00000000-0000-0000-0000-000000000000/resolve' \
  -H 'Content-Type: application/json' \
  -d '{
    "resolution_action": "policy_change",
    "resolution_rationale": "テスト",
    "resolved_by": "test_user"
  }'
```

**期待される結果**:
```json
{
  "detail": "Contradiction not found"
}
```

**検証項目**:
- [ ] HTTPステータス: 404 Not Found
- [ ] エラーメッセージが明確である

---

### Test 2.5: Swagger UI確認

**目的**: Swagger UIで全エンドポイントが確認できることを確認

**実行手順**:
1. ブラウザで`http://localhost:8000/docs`を開く
2. 各タグ配下のエンドポイントを確認

**検証項目**:
- [ ] `contradiction`タグに3つのエンドポイントが表示される
- [ ] `re-evaluation`タグに1つのエンドポイントが表示される
- [ ] `choice-preservation`タグに4つのエンドポイントが表示される
- [ ] `memory-lifecycle`タグに3つのエンドポイントが表示される
- [ ] `dashboard-analytics`タグに3つのエンドポイントが表示される
- [ ] "Try it out"で実際にAPIを実行できる

---

## 3. 統合テスト

### Test 3.1: E2Eフロー - 矛盾検出から解決まで

**目的**: 矛盾検出から解決までの一連のフローが動作することを確認

**シナリオ**:
1. 新しいIntentで矛盾をチェック
2. 矛盾が検出される
3. 矛盾を解決
4. 未解決矛盾一覧から消える

**実行手順**:
```bash
# 1. 矛盾チェック
RESPONSE=$(curl -X POST 'http://localhost:8000/api/v1/contradiction/check' \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": "test_user",
    "intent_id": "e2e-test-001",
    "intent_content": "SQLiteに変更"
  }')

CONTRADICTION_ID=$(echo $RESPONSE | jq -r '.contradictions[0].id')

# 2. 解決
curl -X PUT "http://localhost:8000/api/v1/contradiction/$CONTRADICTION_ID/resolve" \
  -H 'Content-Type: application/json' \
  -d '{
    "resolution_action": "mistake",
    "resolution_rationale": "誤った判断でした",
    "resolved_by": "test_user"
  }'

# 3. 未解決一覧で消えていることを確認
curl -X GET 'http://localhost:8000/api/v1/contradiction/pending?user_id=test_user'
```

**検証項目**:
- [ ] 矛盾が検出される
- [ ] 解決が成功する
- [ ] 未解決一覧から消える

---

### Test 3.2: E2Eフロー - 選択肢作成から決定まで

**目的**: 選択肢の作成から決定までのフローが動作することを確認

**シナリオ**:
1. 選択肢を作成
2. 未決定一覧に表示される
3. 選択を決定（却下理由付き）
4. 検索で取得できる

**実行手順**:
```bash
# 1. 作成
RESPONSE=$(curl -X POST 'http://localhost:8000/api/v1/memory/choice-points/' \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": "test_user",
    "question": "E2Eテスト選択",
    "choices": [
      {"choice_id": "A", "choice_text": "Option A"},
      {"choice_id": "B", "choice_text": "Option B"}
    ],
    "tags": ["e2e-test"]
  }')

CHOICE_POINT_ID=$(echo $RESPONSE | jq -r '.choice_point.id')

# 2. 未決定一覧で確認
curl -X GET 'http://localhost:8000/api/v1/memory/choice-points/pending?user_id=test_user'

# 3. 決定
curl -X PUT "http://localhost:8000/api/v1/memory/choice-points/$CHOICE_POINT_ID/decide" \
  -H 'Content-Type: application/json' \
  -d '{
    "selected_choice_id": "A",
    "decision_rationale": "Aを選択",
    "rejection_reasons": {"B": "Bは不要"}
  }'

# 4. 検索で確認
curl -X GET 'http://localhost:8000/api/v1/memory/choice-points/search?user_id=test_user&tags=e2e-test'
```

**検証項目**:
- [ ] 選択肢が作成される
- [ ] 未決定一覧に表示される
- [ ] 決定が成功する
- [ ] 検索で取得できる
- [ ] 却下理由が保存されている

---

## 4. 後方互換性テスト

### Test 4.1: 既存Messages APIへの影響確認

**目的**: 既存APIが影響を受けていないことを確認

**実行手順**:
```bash
curl -X GET 'http://localhost:8000/api/messages?limit=5' \
  -H 'Content-Type: application/json'
```

**検証項目**:
- [ ] HTTPステータス: 200 OK
- [ ] メッセージが取得できる
- [ ] レスポンス形式が変わっていない

---

### Test 4.2: 既存Intents APIへの影響確認

**目的**: 既存APIが影響を受けていないことを確認

**実行手順**:
```bash
curl -X GET 'http://localhost:8000/api/intents?limit=5' \
  -H 'Content-Type: application/json'
```

**検証項目**:
- [ ] HTTPステータス: 200 OK
- [ ] Intentが取得できる
- [ ] レスポンス形式が変わっていない

---

### Test 4.3: WebSocketへの影響確認

**目的**: WebSocketが影響を受けていないことを確認

**実行手順**:
```bash
python test_websocket.py  # 既存のWebSocketテストスクリプト
```

**検証項目**:
- [ ] WebSocket接続が成功する
- [ ] Ping/Pongが動作する

---

## 5. テスト実行手順

### 5.1 前提条件セットアップ

```bash
# 1. Docker環境起動
cd /Users/zero/Projects/resonant-engine/docker
docker compose up -d

# 2. テストデータ投入
docker exec resonant_postgres psql -U resonant -d resonant_dashboard \
  -f /path/to/test_data.sql
```

### 5.2 自動テスト実行

```bash
# pytest実行
cd /Users/zero/Projects/resonant-engine/backend
pytest tests/integration/test_backend_api_integration.py -v
```

### 5.3 手動テスト実行

上記のcurlコマンドを順番に実行し、結果を確認する。

---

## 6. 成功基準

### ✅ Tier 1テスト（必須）

- [ ] Test 1.1 - 1.10 すべて合格

### ✅ Tier 2テスト（品質）

- [ ] Test 2.1 - 2.5 すべて合格

### ✅ 統合テスト

- [ ] Test 3.1 - 3.2 すべて合格

### ✅ 後方互換性テスト

- [ ] Test 4.1 - 4.3 すべて合格

### ✅ 総合判定

- **合格**: すべてのTier 1テストが合格
- **優秀**: すべてのテストが合格（Tier 1 + Tier 2 + 統合 + 後方互換性）

---

## 7. テスト結果記録

### 7.1 テスト実行記録フォーマット

```markdown
## テスト実行結果 - 2025-11-30

### 実行環境
- Docker version: 24.0.0
- PostgreSQL version: 15.0
- Backend API version: 2.0.0

### Tier 1テスト結果
- Test 1.1: ✅ 合格
- Test 1.2: ✅ 合格
...

### Tier 2テスト結果
- Test 2.1: ✅ 合格（レスポンスタイム: 1.2秒）
...

### 統合テスト結果
- Test 3.1: ✅ 合格
...

### 総合判定
✅ 優秀（全テスト合格）
```

---

## 8. トラブルシューティング

### 問題1: 500 Internal Server Error

**診断**:
```bash
docker logs resonant_backend
```

**一般的な原因**:
- 依存関係の未インストール
- データベース接続エラー
- モジュールimportエラー

### 問題2: 422 Validation Error

**原因**: リクエストボディの形式が不正

**解決策**: 
- Swagger UIでスキーマを確認
- curlコマンドのJSONを検証

---

## 9. 参考資料

- [仕様書](../architecture/backend_api_integration_spec.md)
- [作業開始指示書](../sprint/backend_api_integration_start.md)
- [Contradiction Detection実装](../../../bridge/contradiction/)
- [Memory Store実装](../../../memory_store/)

---

**作成日**: 2025-11-30
**作成者**: Kana (Claude Sonnet 4.5)
**バージョン**: 1.0.0
**総テスト数**: 18件（Tier 1: 10件、Tier 2: 5件、統合: 2件、後方互換: 3件）
