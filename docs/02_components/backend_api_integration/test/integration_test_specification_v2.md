# Backend API統合 統合テスト仕様書 v2.0

**作成日**: 2025-11-30  
**バージョン**: 2.0  
**目的**: Backend API統合の完全な動作確認  
**対象**: 14エンドポイント全テスト

---

## 📋 テスト概要

### テスト範囲

| カテゴリ | エンドポイント数 | テストケース数 |
|---------|----------------|---------------|
| Contradiction Detection | 3 | 6 |
| Re-evaluation | 1 | 2 |
| Choice Preservation | 4 | 8 |
| Memory Lifecycle | 3 | 6 |
| Dashboard Analytics | 3 | 6 |
| **合計** | **14** | **28** |

### 前提条件

- Docker環境起動済み
- PostgreSQL正常動作
- Backend API起動済み（ポート8000）
- schema.sql適用済み

---

## Phase 1: 環境準備（10分）

### Step 1.1: 環境確認

```bash
# Docker起動確認
docker ps | grep resonant
# 期待: resonant_postgres, resonant_backend が表示

# Backend API起動確認
curl http://localhost:8000/health
# 期待: 200 OK

# データベース接続確認
docker exec resonant_postgres psql -U resonant -d resonant_dashboard -c "SELECT version()"
# 期待: PostgreSQL 15.x
```

### Step 1.2: テストデータ準備スクリプト作成

**ファイル**: `tests/data/integration_test_data.sql`

```sql
-- ========================================
-- Backend API統合テスト用データ
-- ========================================

-- 既存のテストデータクリーンアップ
DELETE FROM corrections WHERE intent_id IN (
    SELECT id FROM intents WHERE data->>'user_id' = 'test_integration'
);
DELETE FROM contradictions WHERE user_id = 'test_integration';
DELETE FROM choice_points WHERE user_id = 'test_integration';
DELETE FROM memories WHERE user_id = 'test_integration';
DELETE FROM intents WHERE data->>'user_id' = 'test_integration';

-- ========================================
-- 1. Intent テストデータ（矛盾検出用）
-- ========================================

-- Intent 1: PostgreSQL採用決定（7日前）
INSERT INTO intents (id, source, type, data, status, created_at, updated_at)
VALUES (
    '11111111-1111-1111-1111-111111111111',
    'YUNO',
    'FEATURE_REQUEST',
    jsonb_build_object(
        'user_id', 'test_integration',
        'content', 'データベースとしてPostgreSQLを採用する',
        'intent_text', 'PostgreSQL採用',
        'tech_stack', ARRAY['PostgreSQL'],
        'rationale', 'スケーラビリティとリレーショナルデータ管理'
    ),
    'COMPLETED',
    NOW() - INTERVAL '7 days',
    NOW() - INTERVAL '7 days'
);

-- Intent 2: JWT認証採用（5日前）
INSERT INTO intents (id, source, type, data, status, created_at, updated_at)
VALUES (
    '22222222-2222-2222-2222-222222222222',
    'YUNO',
    'FEATURE_REQUEST',
    jsonb_build_object(
        'user_id', 'test_integration',
        'content', '認証方式としてJWTを採用する',
        'intent_text', 'JWT認証採用',
        'tech_stack', ARRAY['JWT', 'OAuth2'],
        'rationale', 'ステートレス認証の実現'
    ),
    'COMPLETED',
    NOW() - INTERVAL '5 days',
    NOW() - INTERVAL '5 days'
);

-- Intent 3: SQLite検討中（矛盾を起こすIntent、未完了）
INSERT INTO intents (id, source, type, data, status, created_at, updated_at)
VALUES (
    '33333333-3333-3333-3333-333333333333',
    'YUNO',
    'FEATURE_REQUEST',
    jsonb_build_object(
        'user_id', 'test_integration',
        'content', 'パフォーマンス改善のためSQLiteに変更を検討',
        'intent_text', 'SQLite検討',
        'tech_stack', ARRAY['SQLite'],
        'rationale', '軽量化'
    ),
    'PENDING',
    NOW() - INTERVAL '1 day',
    NOW() - INTERVAL '1 day'
);

-- ========================================
-- 2. Contradiction テストデータ
-- ========================================

-- 検出された矛盾: PostgreSQL → SQLite
INSERT INTO contradictions (
    id, user_id, new_intent_id, previous_intent_id,
    contradiction_type, severity, description,
    confidence_score, detected_at
)
VALUES (
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    'test_integration',
    '33333333-3333-3333-3333-333333333333',
    '11111111-1111-1111-1111-111111111111',
    'TECH_STACK',
    'MEDIUM',
    'データベース技術スタックの矛盾: PostgreSQL (7日前) → SQLite (1日前)',
    0.85,
    NOW() - INTERVAL '1 day'
);

-- ========================================
-- 3. Choice Point テストデータ
-- ========================================

-- 未決定の選択肢1: データベース最終決定
INSERT INTO choice_points (
    id, user_id, question, choices,
    tags, context_type, session_id, intent_id,
    created_at, updated_at
)
VALUES (
    'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
    'test_integration',
    'PostgreSQLとSQLiteのどちらを採用するか？',
    jsonb_build_array(
        jsonb_build_object(
            'choice_id', 'A',
            'choice_text', 'PostgreSQLを維持',
            'pros', ARRAY['スケーラブル', 'リレーショナル'],
            'cons', ARRAY['重い']
        ),
        jsonb_build_object(
            'choice_id', 'B',
            'choice_text', 'SQLiteに変更',
            'pros', ARRAY['軽量', '高速'],
            'cons', ARRAY['機能制限']
        )
    ),
    ARRAY['database', 'tech-stack', 'integration-test'],
    'technical',
    '11111111-1111-1111-1111-111111111111',
    '11111111-1111-1111-1111-111111111111',
    NOW() - INTERVAL '2 days',
    NOW() - INTERVAL '2 days'
);

-- 既に決定済みの選択肢: 認証方式
INSERT INTO choice_points (
    id, user_id, question, choices,
    selected_choice_id, decision_rationale,
    tags, context_type, decided_at,
    created_at, updated_at
)
VALUES (
    'cccccccc-cccc-cccc-cccc-cccccccccccc',
    'test_integration',
    '認証方式の選定',
    jsonb_build_array(
        jsonb_build_object(
            'choice_id', 'A',
            'choice_text', 'JWT認証',
            'pros', ARRAY['ステートレス', '拡張性']
        ),
        jsonb_build_object(
            'choice_id', 'B',
            'choice_text', 'セッション認証',
            'pros', ARRAY['シンプル']
        )
    ),
    'A',
    'ステートレス認証の実現とスケーラビリティを優先',
    ARRAY['authentication', 'security'],
    'technical',
    NOW() - INTERVAL '4 days',
    NOW() - INTERVAL '5 days',
    NOW() - INTERVAL '4 days'
);

-- ========================================
-- 4. Memory テストデータ
-- ========================================

-- Working Memory（24時間以内）
INSERT INTO memories (
    content, memory_type, source_type,
    user_id, created_at, expires_at
)
VALUES 
    (
        'PostgreSQL採用を決定した理由: スケーラビリティとACID特性が必要',
        'WORKING',
        'DECISION',
        'test_integration',
        NOW() - INTERVAL '2 hours',
        NOW() + INTERVAL '22 hours'
    ),
    (
        '認証方式としてJWT採用。ステートレス設計を優先',
        'WORKING',
        'DECISION',
        'test_integration',
        NOW() - INTERVAL '5 hours',
        NOW() + INTERVAL '19 hours'
    );

-- Long-term Memory
INSERT INTO memories (
    content, memory_type, source_type,
    user_id, created_at
)
VALUES 
    (
        'プロジェクト開始時の技術スタック検討。PostgreSQL vs MongoDB',
        'LONGTERM',
        'THOUGHT',
        'test_integration',
        NOW() - INTERVAL '30 days'
    );

-- 期限切れMemory（クリーンアップテスト用）
INSERT INTO memories (
    content, memory_type, source_type,
    user_id, created_at, expires_at
)
VALUES 
    (
        '期限切れテストメモリ',
        'WORKING',
        'THOUGHT',
        'test_integration',
        NOW() - INTERVAL '3 days',
        NOW() - INTERVAL '1 day'
    );

-- ========================================
-- 5. Correction テストデータ（Re-evaluation用）
-- ========================================

-- Intent 1への修正履歴
INSERT INTO corrections (
    id, intent_id, correction_id, source, reason, diff, applied_at
)
VALUES (
    'dddddddd-dddd-dddd-dddd-dddddddddddd',
    '11111111-1111-1111-1111-111111111111',
    'dddddddd-dddd-dddd-dddd-dddddddddddd',
    'YUNO',
    'PostgreSQL採用の理由を明確化',
    jsonb_build_object(
        'data.rationale', 'スケーラビリティとリレーショナルデータ管理、ACID特性'
    ),
    NOW() - INTERVAL '6 days'
);

-- ========================================
-- 確認用クエリ
-- ========================================

-- データ投入確認
SELECT 'Intents' as table_name, COUNT(*) as count FROM intents WHERE data->>'user_id' = 'test_integration'
UNION ALL
SELECT 'Contradictions', COUNT(*) FROM contradictions WHERE user_id = 'test_integration'
UNION ALL
SELECT 'Choice Points', COUNT(*) FROM choice_points WHERE user_id = 'test_integration'
UNION ALL
SELECT 'Memories', COUNT(*) FROM memories WHERE user_id = 'test_integration'
UNION ALL
SELECT 'Corrections', COUNT(*) FROM corrections WHERE intent_id IN (
    SELECT id FROM intents WHERE data->>'user_id' = 'test_integration'
);
```

### Step 1.3: テストデータ投入

```bash
# tests/dataディレクトリ作成
mkdir -p /Users/zero/Projects/resonant-engine/tests/data

# スクリプトを作成（上記SQLを保存）

# データ投入
docker exec -i resonant_postgres psql -U resonant -d resonant_dashboard < tests/data/integration_test_data.sql

# 結果確認（期待値）
# Intents: 3
# Contradictions: 1
# Choice Points: 2
# Memories: 4
# Corrections: 1
```

---

## Phase 2: Tier 1テスト実行（30分）

### Test 1: Contradiction Detection API（3エンドポイント）

#### Test 1.1: 未解決矛盾取得

```bash
curl -X GET 'http://localhost:8000/api/v1/contradiction/pending?user_id=test_integration' \
  -H "Content-Type: application/json"
```

**期待される結果**:
```json
{
  "contradictions": [
    {
      "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
      "user_id": "test_integration",
      "contradiction_type": "TECH_STACK",
      "severity": "MEDIUM"
    }
  ],
  "count": 1
}
```

**合格基準**:
- ✅ HTTPステータス: 200 OK
- ✅ count: 1
- ✅ contradiction_type: "TECH_STACK"

---

#### Test 1.2: Intent矛盾チェック

```bash
curl -X POST 'http://localhost:8000/api/v1/contradiction/check' \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_integration",
    "new_intent": {
      "id": "33333333-3333-3333-3333-333333333333",
      "content": "パフォーマンス改善のためSQLiteに変更を検討",
      "tech_stack": ["SQLite"]
    }
  }'
```

**期待される結果**:
```json
{
  "has_contradiction": true,
  "contradictions": [
    {
      "type": "TECH_STACK",
      "severity": "MEDIUM",
      "previous_intent_id": "11111111-1111-1111-1111-111111111111"
    }
  ]
}
```

**合格基準**:
- ✅ HTTPステータス: 200 OK
- ✅ has_contradiction: true

---

#### Test 1.3: 矛盾解決

```bash
curl -X PUT 'http://localhost:8000/api/v1/contradiction/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/resolve' \
  -H "Content-Type: application/json" \
  -d '{
    "resolution": "PostgreSQLを維持することに決定",
    "resolution_action": "reject_new_intent"
  }'
```

**合格基準**:
- ✅ HTTPステータス: 200 OK
- ✅ status: "resolved"

---

### Test 2: Re-evaluation API（1エンドポイント）

```bash
curl -X POST 'http://localhost:8000/api/v1/intent/reeval' \
  -H "Content-Type: application/json" \
  -d '{
    "intent_id": "11111111-1111-1111-1111-111111111111",
    "diff": {
      "data.rationale": "スケーラビリティ、ACID特性、豊富なエコシステム"
    },
    "source": "YUNO",
    "reason": "採用理由をより詳細に記録"
  }'
```

**合格基準**:
- ✅ HTTPステータス: 200 OK
- ✅ status: "CORRECTED"

---

### Test 3: Choice Preservation API（4エンドポイント）

#### Test 3.1: 未決定選択肢取得

```bash
curl -X GET 'http://localhost:8000/api/v1/memory/choice-points/pending?user_id=test_integration'
```

**合格基準**:
- ✅ HTTPステータス: 200 OK
- ✅ count >= 1

#### Test 3.2-3.4: 作成・決定・検索

（完全なコマンド例は長いため省略。上記の統合テスト仕様書に記載）

---

### Test 4: Memory Lifecycle API（3エンドポイント）

```bash
# Test 4.1: ステータス取得
curl 'http://localhost:8000/api/v1/memory/lifecycle/status?user_id=test_integration'

# Test 4.2: 圧縮
curl -X POST 'http://localhost:8000/api/v1/memory/lifecycle/compress?user_id=test_integration'

# Test 4.3: クリーンアップ
curl -X DELETE 'http://localhost:8000/api/v1/memory/lifecycle/cleanup-expired'
```

---

### Test 5: Dashboard Analytics API（3エンドポイント）

```bash
# Test 5.1: システム概要
curl 'http://localhost:8000/api/v1/dashboard/overview'

# Test 5.2: タイムライン
curl 'http://localhost:8000/api/v1/dashboard/timeline?granularity=day'

# Test 5.3: 修正履歴
curl 'http://localhost:8000/api/v1/dashboard/corrections?limit=10'
```

---

## Phase 3: E2Eフローテスト（20分）

### E2E Test 1: 矛盾検出から解決までのフロー

**保存先**: `tests/e2e/contradiction_resolution_flow.sh`

```bash
#!/bin/bash
set -e

echo "E2E Test 1: 矛盾検出から解決まで"

# Step 1: 矛盾チェック
CONTRADICTION_CHECK=$(curl -s -X POST 'http://localhost:8000/api/v1/contradiction/check' \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_integration", "new_intent": {"id": "33333333-3333-3333-3333-333333333333", "content": "SQLiteに変更", "tech_stack": ["SQLite"]}}')

HAS_CONTRADICTION=$(echo $CONTRADICTION_CHECK | jq -r '.has_contradiction')
echo "矛盾検出: $HAS_CONTRADICTION"

if [ "$HAS_CONTRADICTION" != "true" ]; then
  echo "❌ 失敗"
  exit 1
fi

echo "✅ E2E Test 1 合格"
```

---

## 完了基準

- ✅ Tier 1テスト: 14/14 (100%)
- ✅ E2Eテスト: 2/2 (100%)
- ✅ すべてのエンドポイントが200 OK
- ✅ レスポンス形式が仕様通り

---

**作成日**: 2025-11-30  
**バージョン**: 2.0  
**想定作業時間**: 70分
