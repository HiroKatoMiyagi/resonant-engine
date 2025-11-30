# Backend API統合 統合テスト実行指示書

## 概要

**目的**: Backend API統合が完全に完了したことを確認する
**前提**: Phase 2完了（14/14エンドポイント実装済み）
**期間**: 1-2時間
**対象**: 受け入れテスト仕様書の全テストケース実行

---

## 📋 テスト準備

### 前提条件確認

```bash
# 1. Docker環境起動確認
docker ps | grep resonant
# 期待: postgres, backend, frontendコンテナが起動中

# 2. Backend API起動確認
curl http://localhost:8000/health
# 期待: {"status":"healthy",...}

# 3. PostgreSQL接続確認
docker exec resonant_postgres psql -U resonant -d resonant_dashboard -c "SELECT 1"
# 期待: 1
```

---

## Phase 1: テストデータ準備（15分）

### Step 1.1: テストデータ投入スクリプト作成

**ファイル**: `/Users/zero/Projects/resonant-engine/tests/data/test_data.sql`（新規作成）

```sql
-- テストユーザー用データクリーンアップ
DELETE FROM contradictions WHERE user_id = 'test_user';
DELETE FROM choice_points WHERE user_id = 'test_user';
DELETE FROM memories WHERE user_id = 'test_user';
DELETE FROM intents WHERE data->>'user_id' = 'test_user';

-- テスト用Intent作成（矛盾検出用）
INSERT INTO intents (id, source, type, data, status, created_at)
VALUES 
    ('11111111-1111-1111-1111-111111111111', 'YUNO', 'FEATURE_REQUEST', 
     '{"user_id": "test_user", "content": "PostgreSQLを使用する", "intent_text": "PostgreSQLを使用する"}', 
     'COMPLETED', NOW() - INTERVAL '7 days'),
    
    ('22222222-2222-2222-2222-222222222222', 'YUNO', 'FEATURE_REQUEST',
     '{"user_id": "test_user", "content": "認証にJWTを使用", "intent_text": "認証にJWTを使用"}',
     'COMPLETED', NOW() - INTERVAL '5 days');

-- テスト用矛盾データ作成
INSERT INTO contradictions (
    id, user_id, new_intent_id, previous_intent_id,
    contradiction_type, severity, description, detected_at
)
VALUES 
    ('33333333-3333-3333-3333-333333333333', 'test_user', 
     '22222222-2222-2222-2222-222222222222',
     '11111111-1111-1111-1111-111111111111',
     'tech_stack', 'medium', 'データベース選定の矛盾', NOW() - INTERVAL '1 day');

-- テスト用Choice Point作成
INSERT INTO choice_points (
    id, user_id, question, choices, tags, created_at
)
VALUES 
    ('44444444-4444-4444-4444-444444444444', 'test_user',
     'データベース選定',
     '[
        {"choice_id": "A", "choice_text": "PostgreSQL"},
        {"choice_id": "B", "choice_text": "SQLite"}
     ]'::jsonb,
     ARRAY['technology', 'database'],
     NOW() - INTERVAL '2 days');

-- テスト用メモリデータ
INSERT INTO memories (content, memory_type, user_id, created_at)
VALUES 
    ('テストメモリ1', 'WORKING', 'test_user', NOW()),
    ('テストメモリ2', 'LONGTERM', 'test_user', NOW() - INTERVAL '30 days');
```

### Step 1.2: テストデータ投入

```bash
cd /Users/zero/Projects/resonant-engine
docker exec -i resonant_postgres psql -U resonant -d resonant_dashboard < tests/data/test_data.sql
```

**確認**:
```bash
docker exec resonant_postgres psql -U resonant -d resonant_dashboard -c "SELECT COUNT(*) FROM intents WHERE data->>'user_id' = 'test_user'"
# 期待: 2
```

---

## Phase 2: Tier 1テスト実行（30分）

### Test 1.1: Contradiction Detection - 未解決矛盾取得

```bash
curl -X GET 'http://localhost:8000/api/v1/contradiction/pending?user_id=test_user' \
  -H 'Content-Type: application/json' | jq
```

**期待される結果**:
```json
{
  "contradictions": [
    {
      "id": "33333333-3333-3333-3333-333333333333",
      "user_id": "test_user",
      "contradiction_type": "tech_stack",
      "severity": "medium"
    }
  ],
  "count": 1
}
```

**検証**:
- [ ] HTTPステータス: 200 OK
- [ ] `count`が1である
- [ ] 矛盾データが返される

---

### Test 1.2: Contradiction Detection - Intent矛盾チェック

```bash
curl -X POST 'http://localhost:8000/api/v1/contradiction/check' \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": "test_user",
    "intent_id": "new-intent-001",
    "intent_content": "SQLiteに変更する"
  }' | jq
```

**期待される結果**:
```json
{
  "contradictions": [
    {
      "contradiction_type": "tech_stack",
      "confidence_score": 0.85,
      "details": {...}
    }
  ],
  "count": 1
}
```

**検証**:
- [ ] HTTPステータス: 200 OK
- [ ] 矛盾が検出される（PostgreSQL→SQLiteの矛盾）

---

### Test 1.3: Contradiction Detection - 矛盾解決

```bash
curl -X PUT 'http://localhost:8000/api/v1/contradiction/33333333-3333-3333-3333-333333333333/resolve' \
  -H 'Content-Type: application/json' \
  -d '{
    "resolution_action": "policy_change",
    "resolution_rationale": "要件変更により方針転換",
    "resolved_by": "test_user"
  }' | jq
```

**期待される結果**:
```json
{
  "status": "resolved",
  "contradiction_id": "33333333-3333-3333-3333-333333333333",
  "resolution_action": "policy_change"
}
```

**検証**:
- [ ] HTTPステータス: 200 OK
- [ ] `status`が"resolved"である

---

### Test 1.4: Re-evaluation - Intent再評価

```bash
curl -X POST 'http://localhost:8000/api/v1/intent/reeval' \
  -H 'Content-Type: application/json' \
  -d '{
    "intent_id": "11111111-1111-1111-1111-111111111111",
    "diff": {"priority": 10},
    "source": "YUNO",
    "reason": "優先度を上げる"
  }' | jq
```

**期待される結果**:
```json
{
  "intent_id": "11111111-1111-1111-1111-111111111111",
  "status": "re-evaluated",
  "result": {...}
}
```

**検証**:
- [ ] HTTPステータス: 200 OK
- [ ] `status`が"re-evaluated"である

---

### Test 1.5: Choice Preservation - 未決定選択肢取得

```bash
curl -X GET 'http://localhost:8000/api/v1/memory/choice-points/pending?user_id=test_user' \
  -H 'Content-Type: application/json' | jq
```

**期待される結果**:
```json
{
  "choice_points": [
    {
      "id": "44444444-4444-4444-4444-444444444444",
      "question": "データベース選定",
      "selected_choice_id": null
    }
  ],
  "count": 1
}
```

**検証**:
- [ ] HTTPステータス: 200 OK
- [ ] `count`が1である
- [ ] `selected_choice_id`がnullである

---

### Test 1.6: Choice Preservation - 選択肢作成

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
  }' | jq
```

**期待される結果**:
```json
{
  "choice_point": {
    "id": "...",
    "question": "認証方式選定",
    "tags": ["security", "authentication"]
  }
}
```

**検証**:
- [ ] HTTPステータス: 200 OK
- [ ] `choice_point.id`が生成されている
- [ ] `tags`が保存されている

**次のテストのためにIDを保存**:
```bash
NEW_CHOICE_POINT_ID=$(curl -s -X POST 'http://localhost:8000/api/v1/memory/choice-points/' \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": "test_user",
    "question": "認証方式選定",
    "choices": [
      {"choice_id": "A", "choice_text": "JWT"},
      {"choice_id": "B", "choice_text": "Session"}
    ],
    "tags": ["security"]
  }' | jq -r '.choice_point.id')

echo "New Choice Point ID: $NEW_CHOICE_POINT_ID"
```

---

### Test 1.7: Choice Preservation - 選択決定（却下理由付き）

```bash
curl -X PUT "http://localhost:8000/api/v1/memory/choice-points/$NEW_CHOICE_POINT_ID/decide" \
  -H 'Content-Type: application/json' \
  -d '{
    "selected_choice_id": "A",
    "decision_rationale": "スケーラビリティと標準化を考慮",
    "rejection_reasons": {
      "B": "セッション管理の複雑さとスケーラビリティ限界"
    }
  }' | jq
```

**期待される結果**:
```json
{
  "choice_point": {
    "selected_choice_id": "A",
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
    "decided_at": "..."
  }
}
```

**検証**:
- [ ] HTTPステータス: 200 OK
- [ ] `selected_choice_id`が"A"である
- [ ] 選択肢Bの`rejection_reason`が保存されている

---

### Test 1.8: Choice Preservation - 検索（タグフィルタ）

```bash
curl -X GET 'http://localhost:8000/api/v1/memory/choice-points/search?user_id=test_user&tags=security&limit=10' \
  -H 'Content-Type: application/json' | jq
```

**期待される結果**:
```json
{
  "results": [
    {
      "question": "認証方式選定",
      "tags": ["security"],
      "selected_choice_id": "A"
    }
  ],
  "count": 1
}
```

**検証**:
- [ ] HTTPステータス: 200 OK
- [ ] タグが一致する選択肢が返る

---

### Test 1.9: Memory Lifecycle - ステータス取得

```bash
curl -X GET 'http://localhost:8000/api/v1/memory/lifecycle/status?user_id=test_user' \
  -H 'Content-Type: application/json' | jq
```

**期待される結果**:
```json
{
  "user_id": "test_user",
  "total_memories": 2,
  "working_memory_count": 1,
  "longterm_memory_count": 1,
  "capacity_used_percentage": 0.002
}
```

**検証**:
- [ ] HTTPステータス: 200 OK
- [ ] `total_memories`が2である

---

### Test 1.10: Dashboard Analytics - システム概要

```bash
curl -X GET 'http://localhost:8000/api/v1/dashboard/overview' \
  -H 'Content-Type: application/json' | jq
```

**期待される結果**:
```json
{
  "messages_count": 0,
  "intents_count": 2,
  "active_sessions": 0,
  "contradictions_pending": 0,
  "crisis_index": 0
}
```

**検証**:
- [ ] HTTPステータス: 200 OK
- [ ] 全フィールドが存在する

---

## Phase 3: Tier 2テスト実行（20分）

### Test 2.1: パフォーマンス - 矛盾検出

```bash
time curl -X POST 'http://localhost:8000/api/v1/contradiction/check' \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": "test_user",
    "intent_id": "perf-test-001",
    "intent_content": "パフォーマンステスト"
  }' > /dev/null 2>&1
```

**検証**:
- [ ] レスポンスタイム < 2秒

---

### Test 2.2: パフォーマンス - 選択肢検索

```bash
time curl -X GET 'http://localhost:8000/api/v1/memory/choice-points/search?user_id=test_user&limit=100' \
  -H 'Content-Type: application/json' > /dev/null 2>&1
```

**検証**:
- [ ] レスポンスタイム < 500ms

---

### Test 2.3: エラーハンドリング - 無効なユーザーID

```bash
curl -X GET 'http://localhost:8000/api/v1/contradiction/pending?user_id=' \
  -H 'Content-Type: application/json' | jq
```

**期待される結果**:
```json
{
  "detail": [
    {
      "loc": ["query", "user_id"],
      "msg": "field required"
    }
  ]
}
```

**検証**:
- [ ] HTTPステータス: 422 Unprocessable Entity

---

### Test 2.4: Swagger UI確認

```bash
open http://localhost:8000/docs
```

**手動確認項目**:
- [ ] `contradiction`タグに3エンドポイント表示
- [ ] `re-evaluation`タグに1エンドポイント表示
- [ ] `choice-preservation`タグに4エンドポイント表示
- [ ] `memory-lifecycle`タグに3エンドポイント表示
- [ ] `dashboard-analytics`タグに3エンドポイント表示
- [ ] "Try it out"で実行可能

---

## Phase 4: E2Eテスト実行（20分）

### Test 3.1: E2Eフロー - 矛盾検出から解決まで

```bash
#!/bin/bash
# e2e_contradiction_test.sh

echo "=== E2E Test: Contradiction Detection ==="

# 1. 矛盾チェック
echo "1. Checking for contradictions..."
RESPONSE=$(curl -s -X POST 'http://localhost:8000/api/v1/contradiction/check' \
  -H 'Content-Type: application/json' \
  -d '{
    "user_id": "test_user",
    "intent_id": "e2e-test-001",
    "intent_content": "MongoDBに変更する"
  }')

echo $RESPONSE | jq

# 矛盾が検出されたか確認
COUNT=$(echo $RESPONSE | jq '.count')
if [ "$COUNT" -gt 0 ]; then
    echo "✅ Contradiction detected"
else
    echo "❌ No contradiction detected"
    exit 1
fi

# 2. 未解決矛盾を確認
echo "2. Getting pending contradictions..."
PENDING=$(curl -s 'http://localhost:8000/api/v1/contradiction/pending?user_id=test_user')
echo $PENDING | jq

echo "✅ E2E Test Passed"
```

実行:
```bash
chmod +x e2e_contradiction_test.sh
./e2e_contradiction_test.sh
```

---

### Test 3.2: E2Eフロー - 選択肢作成から決定まで

```bash
#!/bin/bash
# e2e_choice_test.sh

echo "=== E2E Test: Choice Preservation ==="

# 1. 選択肢作成
echo "1. Creating choice point..."
RESPONSE=$(curl -s -X POST 'http://localhost:8000/api/v1/memory/choice-points/' \
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
echo "Created: $CHOICE_POINT_ID"

# 2. 未決定一覧で確認
echo "2. Checking pending list..."
curl -s 'http://localhost:8000/api/v1/memory/choice-points/pending?user_id=test_user' | jq

# 3. 決定
echo "3. Deciding choice..."
curl -s -X PUT "http://localhost:8000/api/v1/memory/choice-points/$CHOICE_POINT_ID/decide" \
  -H 'Content-Type: application/json' \
  -d '{
    "selected_choice_id": "A",
    "decision_rationale": "Aを選択",
    "rejection_reasons": {"B": "Bは不要"}
  }' | jq

# 4. 検索で確認
echo "4. Searching..."
SEARCH=$(curl -s 'http://localhost:8000/api/v1/memory/choice-points/search?user_id=test_user&tags=e2e-test')
echo $SEARCH | jq

# 却下理由が保存されているか確認
REJECTION=$(echo $SEARCH | jq -r '.results[0].choices[] | select(.choice_id == "B") | .rejection_reason')
if [ "$REJECTION" == "Bは不要" ]; then
    echo "✅ Rejection reason saved"
else
    echo "❌ Rejection reason not saved"
    exit 1
fi

echo "✅ E2E Test Passed"
```

実行:
```bash
chmod +x e2e_choice_test.sh
./e2e_choice_test.sh
```

---

## Phase 5: 後方互換性テスト（10分）

### Test 4.1: 既存Messages API

```bash
curl -X GET 'http://localhost:8000/api/messages?limit=5' | jq
```

**検証**:
- [ ] HTTPステータス: 200 OK
- [ ] レスポンス形式が変わっていない

---

### Test 4.2: 既存Intents API

```bash
curl -X GET 'http://localhost:8000/api/intents?limit=5' | jq
```

**検証**:
- [ ] HTTPステータス: 200 OK
- [ ] レスポンス形式が変わっていない

---

## テスト結果記録

### 結果記録フォーマット

**ファイル**: `/Users/zero/Projects/resonant-engine/docs/reports/integration_test_results_YYYYMMDD.md`

```markdown
# Backend API統合テスト結果

**実行日**: 2025-11-30
**実行者**: [名前]
**環境**: Docker環境

## Tier 1テスト結果

| Test ID | テスト名 | 結果 | 備考 |
|---------|---------|------|------|
| 1.1 | Contradiction - 未解決取得 | ✅ | count=1 |
| 1.2 | Contradiction - チェック | ✅ | 矛盾検出成功 |
| 1.3 | Contradiction - 解決 | ✅ | |
| 1.4 | Re-evaluation | ✅ | |
| 1.5 | Choice - 未決定取得 | ✅ | count=1 |
| 1.6 | Choice - 作成 | ✅ | |
| 1.7 | Choice - 決定 | ✅ | 却下理由保存確認 |
| 1.8 | Choice - 検索 | ✅ | |
| 1.9 | Memory Lifecycle | ✅ | |
| 1.10 | Dashboard Analytics | ✅ | |

## Tier 2テスト結果

| Test ID | テスト名 | 結果 | パフォーマンス |
|---------|---------|------|--------------|
| 2.1 | パフォーマンス - 矛盾検出 | ✅ | 1.2秒 |
| 2.2 | パフォーマンス - 選択検索 | ✅ | 0.3秒 |
| 2.3 | エラーハンドリング | ✅ | 422返却 |
| 2.4 | Swagger UI | ✅ | 全表示確認 |

## E2Eテスト結果

| Test ID | テスト名 | 結果 | 備考 |
|---------|---------|------|------|
| 3.1 | 矛盾検出フロー | ✅ | |
| 3.2 | 選択肢フロー | ✅ | 却下理由保存確認 |

## 後方互換性テスト結果

| Test ID | テスト名 | 結果 | 備考 |
|---------|---------|------|------|
| 4.1 | Messages API | ✅ | 影響なし |
| 4.2 | Intents API | ✅ | 影響なし |

## 総合判定

✅ **全テスト合格（18/18）**

エンドポイント動作率: **14/14 (100%)**
Tier 1達成率: **10/10 (100%)**
Tier 2達成率: **4/4 (100%)**

## 備考

- Phase 2完了により全エンドポイント動作確認
- パフォーマンス目標達成
- 既存APIへの影響なし
```

---

## 完了基準

### ✅ 統合テスト完了判定

- [ ] Tier 1テスト: 10/10合格
- [ ] Tier 2テスト: 4/4合格
- [ ] E2Eテスト: 2/2合格
- [ ] 後方互換性テスト: 2/2合格
- [ ] テスト結果レポート作成完了

### 📊 最終達成率

**統合テスト完了後**:
- エンドポイント: **14/14 (100%)** ✅
- Tier 1要件: **8/8 (100%)** ✅
- Tier 2要件: **5/5 (100%)** ✅
- **Backend API統合: 完全完了** ✅

---

## 次のステップ

統合テスト完了後:

1. **Frontend更新**: 仕様書修正、APIクライアント更新
2. **本番デプロイ準備**: Oracle Cloud環境構築
3. **ドキュメント最終化**: 実装完了レポート更新

---

**作成日**: 2025-11-30
**想定時間**: 1-2時間
**対象**: Backend API統合の完全性確認
