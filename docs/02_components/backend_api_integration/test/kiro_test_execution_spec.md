# Backend API統合テスト実行仕様書（Kiro用）

**作成日**: 2025-12-02  
**対象**: Kiro (Claude Sonnet 4.5 via Cursor)  
**目的**: Backend API統合の動作確認を、指定された手順通りに実行  
**想定時間**: 60分

---

## ⚠️ CRITICAL: 実行ルール

### 必須遵守事項

1. **この仕様書に書かれたコマンドのみを実行する**
   - ❌ 自分で考えたコマンドを実行しない
   - ❌ ファイルを勝手に編集しない
   - ❌ SQLクエリを勝手に変更しない

2. **各Phaseの終わりで必ず停止して報告する**
   - ✅ 実行したコマンド
   - ✅ 実際の出力結果（全文コピー）
   - ✅ 成功/失敗の判定
   - ⚠️ 次のPhaseに進む前に宏啓さんの確認を待つ

3. **エラーが出たら即座に停止する**
   - ❌ エラーを無視して進まない
   - ❌ 自分で修正しない
   - ✅ エラー内容を完全にコピーして報告
   - ✅ 宏啓さんの指示を待つ

4. **期待値と実際の出力が異なる場合は停止する**
   - ❌ 「だいたい合ってる」で進まない
   - ✅ 差異を報告して指示を待つ

5. **ハルシネーション（存在しないファイル・機能への言及）厳禁**
   - ✅ 実際に存在するファイルのみを扱う
   - ✅ 存在を確認してから言及する
   - ❌ 「～があるはず」「～すべき」は禁止

### 禁止事項

```yaml
禁止:
  - コード修正
  - ファイル作成・削除（テストデータを除く）
  - スキーマ変更
  - ライブラリのインストール・アップグレード
  - Docker設定の変更
  - 環境変数の変更
  - この仕様書に記載されていないコマンドの実行

許可:
  - この仕様書に記載されたコマンドの実行
  - ファイルの読み取り（viewコマンド）
  - テストデータ投入（指定されたSQLファイル）
  - curl/HTTPリクエスト実行
  - 実行結果の報告
```

---

## Phase 0: 事前確認（5分）

### 目的
現在の環境状態を確認し、テスト開始可能かを判定する。

### Step 0.1: プロジェクトディレクトリ確認

**実行コマンド**:
```bash
cd /Users/zero/Projects/resonant-engine && pwd
```

**期待される出力**:
```
/Users/zero/Projects/resonant-engine
```

**判定基準**:
- ✅ 成功: `/Users/zero/Projects/resonant-engine`が表示される
- ❌ 失敗: 別のパスが表示される、またはエラー

---

### Step 0.2: 必要ファイルの存在確認

**実行コマンド**:
```bash
cd /Users/zero/Projects/resonant-engine && \
ls -la backend/app/routers/contradictions.py \
        backend/app/routers/choice_points.py \
        backend/app/routers/re_evaluation.py \
        backend/app/routers/memory_lifecycle.py \
        tests/data/integration_test_data_v2.sql
```

**期待される出力**:
```
-rw-r--r--  1 zero  staff  XXXX ... backend/app/routers/contradictions.py
-rw-r--r--  1 zero  staff  XXXX ... backend/app/routers/choice_points.py
-rw-r--r--  1 zero  staff  XXXX ... backend/app/routers/re_evaluation.py
-rw-r--r--  1 zero  staff  XXXX ... backend/app/routers/memory_lifecycle.py
-rw-r--r--  1 zero  staff  XXXX ... tests/data/integration_test_data_v2.sql
```

**判定基準**:
- ✅ 成功: 5つのファイルすべてが存在する
- ❌ 失敗: いずれかのファイルが存在しない（"No such file or directory"）

---

### Step 0.3: Dockerコマンド確認

**実行コマンド**:
```bash
docker --version
```

**期待される出力**:
```
Docker version XX.XX.X, build XXXXXXX
```

**判定基準**:
- ✅ 成功: バージョン情報が表示される
- ❌ 失敗: "command not found"または エラー

---

### 📊 Phase 0 報告テンプレート

```markdown
## Phase 0: 事前確認 - 完了報告

### Step 0.1: プロジェクトディレクトリ確認
実行: `cd /Users/zero/Projects/resonant-engine && pwd`
出力: [ここに実際の出力を貼り付け]
判定: ✅成功 / ❌失敗

### Step 0.2: 必要ファイルの存在確認
実行: `ls -la backend/app/routers/...`
出力: [ここに実際の出力を貼り付け]
判定: ✅成功 / ❌失敗

### Step 0.3: Dockerコマンド確認
実行: `docker --version`
出力: [ここに実際の出力を貼り付け]
判定: ✅成功 / ❌失敗

**Phase 0 総合判定**: ✅全成功 / ❌一部失敗

[一部失敗の場合は、次のPhaseに進まず、宏啓さんの指示を待つ]
```

---

## Phase 1: Docker環境構築（10分）

### 目的
テスト実行に必要なDocker環境を起動する。

### Step 1.1: 既存コンテナの停止

**実行コマンド**:
```bash
cd /Users/zero/Projects/resonant-engine/docker && \
docker compose down
```

**期待される出力**:
```
[+] Running X/X
 ✔ Container resonant_backend   Removed
 ✔ Container resonant_postgres  Removed
 ✔ Network docker_default       Removed
```

**判定基準**:
- ✅ 成功: "Removed"が表示される、または既にコンテナが存在しない
- ⚠️ 警告: "No such container"は問題なし（既に停止済み）
- ❌ 失敗: エラーメッセージが表示される

---

### Step 1.2: Dockerコンテナ起動

**実行コマンド**:
```bash
cd /Users/zero/Projects/resonant-engine/docker && \
docker compose up -d
```

**期待される出力**:
```
[+] Running X/X
 ✔ Container resonant_postgres  Started
 ✔ Container resonant_backend   Started
```

**判定基準**:
- ✅ 成功: "Started"が2つ表示される
- ❌ 失敗: "Error"または "failed"が表示される

**⚠️ エラー時の対応**:
- エラーメッセージを全文コピーして報告
- 次のコマンドを実行せずに停止

---

### Step 1.3: コンテナ起動確認（30秒待機）

**実行コマンド**:
```bash
sleep 30 && docker ps | grep resonant
```

**期待される出力**:
```
CONTAINER ID   IMAGE              ...   STATUS         ...   NAMES
xxxxxxxxxxxx   resonant_backend   ...   Up 30 seconds  ...   resonant_backend
xxxxxxxxxxxx   postgres:15-alpine ...   Up 30 seconds  ...   resonant_postgres
```

**判定基準**:
- ✅ 成功: 2つのコンテナが"Up"状態
- ❌ 失敗: コンテナが表示されない、または"Exited"状態

---

### Step 1.4: Backend APIヘルスチェック

**実行コマンド**:
```bash
curl -s http://localhost:8000/health
```

**期待される出力**:
```json
{"status":"ok"}
```

**判定基準**:
- ✅ 成功: `{"status":"ok"}`が返る
- ❌ 失敗: 接続エラー、または異なるレスポンス

**⚠️ エラー時の対応**:
```bash
# ログ確認コマンド（報告用）
docker logs resonant_backend --tail 50
```

---

### Step 1.5: PostgreSQL接続確認

**実行コマンド**:
```bash
docker exec resonant_postgres psql -U resonant -d resonant_dashboard -c "SELECT version();"
```

**期待される出力**:
```
                                                 version
---------------------------------------------------------------------------------------------------------
 PostgreSQL 15.X on x86_64-pc-linux-musl, compiled by gcc (Alpine ...) ..., 64-bit
(1 row)
```

**判定基準**:
- ✅ 成功: "PostgreSQL 15"を含むバージョン情報が表示される
- ❌ 失敗: 接続エラー、または異なるバージョン

---

### 📊 Phase 1 報告テンプレート

```markdown
## Phase 1: Docker環境構築 - 完了報告

### Step 1.1: 既存コンテナの停止
実行: `docker compose down`
出力: [ここに実際の出力を貼り付け]
判定: ✅成功 / ⚠️警告 / ❌失敗

### Step 1.2: Dockerコンテナ起動
実行: `docker compose up -d`
出力: [ここに実際の出力を貼り付け]
判定: ✅成功 / ❌失敗

### Step 1.3: コンテナ起動確認
実行: `docker ps | grep resonant`
出力: [ここに実際の出力を貼り付け]
判定: ✅成功 / ❌失敗

### Step 1.4: Backend APIヘルスチェック
実行: `curl http://localhost:8000/health`
出力: [ここに実際の出力を貼り付け]
判定: ✅成功 / ❌失敗

### Step 1.5: PostgreSQL接続確認
実行: `docker exec ... SELECT version()`
出力: [ここに実際の出力を貼り付け]
判定: ✅成功 / ❌失敗

**Phase 1 総合判定**: ✅全成功 / ❌一部失敗

[失敗がある場合は停止]
```

---

## Phase 2: テストデータ投入（5分）

### 目的
APIテストに必要なテストデータをPostgreSQLに投入する。

### Step 2.1: 既存テストデータのクリーンアップ

**実行コマンド**:
```bash
docker exec resonant_postgres psql -U resonant -d resonant_dashboard -c "
DELETE FROM corrections WHERE intent_id IN (
    SELECT id FROM intents WHERE data->>'user_id' = 'test_integration'
);
DELETE FROM contradictions WHERE user_id = 'test_integration';
DELETE FROM choice_points WHERE user_id = 'test_integration';
DELETE FROM memories WHERE user_id = 'test_integration';
DELETE FROM intents WHERE data->>'user_id' = 'test_integration';
"
```

**期待される出力**:
```
DELETE X
DELETE X
DELETE X
DELETE X
DELETE X
```

**判定基準**:
- ✅ 成功: "DELETE"が5行表示される（Xは0でもOK）
- ❌ 失敗: エラーメッセージが表示される

---

### Step 2.2: テストデータ投入

**実行コマンド**:
```bash
docker exec -i resonant_postgres psql -U resonant -d resonant_dashboard < /Users/zero/Projects/resonant-engine/tests/data/integration_test_data_v2.sql
```

**期待される出力**:
```
DELETE X
DELETE X
...
INSERT 0 1
INSERT 0 1
...
 table_name   | count
--------------+-------
 Intents      |     3
 Contradictions|    1
 Choice Points|     2
 Memories     |     4
 Corrections  |     1
(5 rows)
```

**判定基準**:
- ✅ 成功: 最後に5行のテーブルとカウントが表示される
- ✅ 期待値:
  - Intents: 3
  - Contradictions: 1
  - Choice Points: 2
  - Memories: 4
  - Corrections: 1
- ❌ 失敗: エラーメッセージ、またはカウントが異なる

---

### Step 2.3: データ投入確認

**実行コマンド**:
```bash
docker exec resonant_postgres psql -U resonant -d resonant_dashboard -c "
SELECT 'Intents' as table_name, COUNT(*) as count 
FROM intents WHERE data->>'user_id' = 'test_integration'
UNION ALL
SELECT 'Contradictions', COUNT(*) 
FROM contradictions WHERE user_id = 'test_integration'
UNION ALL
SELECT 'Choice Points', COUNT(*) 
FROM choice_points WHERE user_id = 'test_integration'
UNION ALL
SELECT 'Memories', COUNT(*) 
FROM memories WHERE user_id = 'test_integration';
"
```

**期待される出力**:
```
   table_name   | count
----------------+-------
 Intents        |     3
 Contradictions |     1
 Choice Points  |     2
 Memories       |     4
(4 rows)
```

**判定基準**:
- ✅ 成功: 上記の通りのカウント
- ❌ 失敗: カウントが異なる、またはエラー

---

### 📊 Phase 2 報告テンプレート

```markdown
## Phase 2: テストデータ投入 - 完了報告

### Step 2.1: 既存テストデータのクリーンアップ
実行: `docker exec ... DELETE FROM ...`
出力: [ここに実際の出力を貼り付け]
判定: ✅成功 / ❌失敗

### Step 2.2: テストデータ投入
実行: `docker exec -i ... < integration_test_data_v2.sql`
出力: [ここに実際の出力を貼り付け]
判定: ✅成功 / ❌失敗
カウント確認:
- Intents: 実際=X, 期待=3 [✅/❌]
- Contradictions: 実際=X, 期待=1 [✅/❌]
- Choice Points: 実際=X, 期待=2 [✅/❌]
- Memories: 実際=X, 期待=4 [✅/❌]
- Corrections: 実際=X, 期待=1 [✅/❌]

### Step 2.3: データ投入確認
実行: `docker exec ... SELECT 'Intents' ...`
出力: [ここに実際の出力を貼り付け]
判定: ✅成功 / ❌失敗

**Phase 2 総合判定**: ✅全成功 / ❌一部失敗

[失敗がある場合は停止]
```

---

## Phase 3: API実行テスト（30分）

### 目的
各APIエンドポイントが正しく動作することを確認する。

### Test 3.1: Contradiction Detection - 未解決矛盾取得

**実行コマンド**:
```bash
curl -s -X GET 'http://localhost:8000/api/v1/contradiction/pending?user_id=test_integration' | jq
```

**期待される出力**:
```json
{
  "contradictions": [
    {
      "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
      "user_id": "test_integration",
      "new_intent_id": "33333333-3333-3333-3333-333333333333",
      "contradiction_type": "TECH_STACK",
      "confidence_score": 0.85,
      ...
    }
  ],
  "count": 1
}
```

**判定基準**:
- ✅ HTTPステータス: 200（エラーなし）
- ✅ count: 1
- ✅ contradiction_type: "TECH_STACK"
- ✅ user_id: "test_integration"
- ❌ 失敗: エラーメッセージ、count != 1、またはフィールド不足

---

### Test 3.2: Contradiction Detection - Intentチェック

**実行コマンド**:
```bash
curl -s -X POST 'http://localhost:8000/api/v1/contradiction/check' \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_integration",
    "intent_id": "33333333-3333-3333-3333-333333333333",
    "intent_content": "パフォーマンス改善のためSQLiteに変更を検討"
  }' | jq
```

**期待される出力**:
```json
{
  "contradictions": [
    {
      "contradiction_type": "TECH_STACK",
      "conflicting_intent_id": "11111111-1111-1111-1111-111111111111",
      ...
    }
  ],
  "count": 1
}
```

**判定基準**:
- ✅ HTTPステータス: 200
- ✅ count >= 1
- ✅ contradiction_type: "TECH_STACK"
- ❌ 失敗: エラー、またはcount = 0

---

### Test 3.3: Contradiction Detection - 矛盾解決

**実行コマンド**:
```bash
curl -s -X PUT 'http://localhost:8000/api/v1/contradiction/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/resolve' \
  -H "Content-Type: application/json" \
  -d '{
    "resolution_action": "policy_change",
    "resolution_rationale": "PostgreSQLを維持することに決定",
    "resolved_by": "test_integration"
  }' | jq
```

**期待される出力**:
```json
{
  "status": "resolved",
  "contradiction_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
  "resolution_action": "policy_change"
}
```

**判定基準**:
- ✅ HTTPステータス: 200
- ✅ status: "resolved"
- ❌ 失敗: エラー、または異なるレスポンス

---

### Test 3.4: Re-evaluation - Intent再評価

**実行コマンド**:
```bash
curl -s -X POST 'http://localhost:8000/api/v1/intent/reeval' \
  -H "Content-Type: application/json" \
  -d '{
    "intent_id": "11111111-1111-1111-1111-111111111111",
    "diff": {
      "data.rationale": "スケーラビリティ、ACID特性、豊富なエコシステム"
    },
    "source": "YUNO",
    "reason": "採用理由をより詳細に記録"
  }' | jq
```

**期待される出力**:
```json
{
  "intent_id": "11111111-1111-1111-1111-111111111111",
  "status": "re-evaluated",
  "result": { ... }
}
```

**判定基準**:
- ✅ HTTPステータス: 200
- ✅ intent_id が一致
- ✅ status フィールドが存在
- ❌ 失敗: エラー、またはフィールド不足

---

### Test 3.5: Choice Preservation - 未決定選択肢取得

**実行コマンド**:
```bash
curl -s -X GET 'http://localhost:8000/api/v1/memory/choice-points/pending?user_id=test_integration' | jq
```

**期待される出力**:
```json
{
  "choice_points": [
    {
      "id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
      "user_id": "test_integration",
      "question": "PostgreSQLとSQLiteのどちらを採用するか？",
      ...
    }
  ],
  "count": 1
}
```

**判定基準**:
- ✅ HTTPステータス: 200
- ✅ count >= 1
- ✅ selected_choice_id が null（未決定）
- ❌ 失敗: エラー、またはcount = 0

---

### Test 3.6: Choice Preservation - 選択肢作成

**実行コマンド**:
```bash
curl -s -X POST 'http://localhost:8000/api/v1/memory/choice-points/' \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_integration",
    "question": "認証方式の選定（テスト）",
    "choices": [
      {"choice_id": "A", "choice_text": "JWT認証"},
      {"choice_id": "B", "choice_text": "セッション認証"}
    ],
    "tags": ["test", "authentication"],
    "context_type": "technical"
  }' | jq
```

**期待される出力**:
```json
{
  "choice_point": {
    "id": "...",
    "user_id": "test_integration",
    "question": "認証方式の選定（テスト）",
    "choices": [ ... ],
    ...
  }
}
```

**判定基準**:
- ✅ HTTPステータス: 200
- ✅ choice_point.id が存在
- ✅ question が一致
- ❌ 失敗: エラー、またはフィールド不足

**⚠️ 重要**: 次のテストで使うため、`choice_point.id`の値を記録する

---

### Test 3.7: Choice Preservation - 選択決定

**実行コマンド**:
```bash
# ⚠️ {choice_point_id} を Test 3.6 で取得したIDに置き換える
curl -s -X PUT 'http://localhost:8000/api/v1/memory/choice-points/{choice_point_id}/decide' \
  -H "Content-Type: application/json" \
  -d '{
    "selected_choice_id": "A",
    "decision_rationale": "JWT認証を採用（ステートレス設計）",
    "rejection_reasons": {
      "B": "スケーラビリティに課題"
    }
  }' | jq
```

**期待される出力**:
```json
{
  "choice_point": {
    "id": "...",
    "selected_choice_id": "A",
    "decision_rationale": "JWT認証を採用（ステートレス設計）",
    "decided_at": "2025-12-02T...",
    ...
  }
}
```

**判定基準**:
- ✅ HTTPステータス: 200
- ✅ selected_choice_id: "A"
- ✅ decided_at が存在（null でない）
- ❌ 失敗: エラー、またはフィールド不足

---

### Test 3.8: Choice Preservation - 検索

**実行コマンド**:
```bash
curl -s -X GET 'http://localhost:8000/api/v1/memory/choice-points/search?user_id=test_integration&tags=test&limit=10' | jq
```

**期待される出力**:
```json
{
  "results": [
    {
      "id": "...",
      "question": "認証方式の選定（テスト）",
      "selected_choice_id": "A",
      ...
    }
  ],
  "count": 1
}
```

**判定基準**:
- ✅ HTTPステータス: 200
- ✅ count >= 1
- ✅ selected_choice_id が "A"
- ❌ 失敗: エラー、またはcount = 0

---

### Test 3.9: Memory Lifecycle - ステータス取得

**実行コマンド**:
```bash
curl -s -X GET 'http://localhost:8000/api/v1/memory/lifecycle/status?user_id=test_integration' | jq
```

**期待される出力**:
```json
{
  "user_id": "test_integration",
  "total_memories": 4,
  "working_memories": 2,
  "longterm_memories": 2,
  "capacity_used": "...",
  ...
}
```

**判定基準**:
- ✅ HTTPステータス: 200
- ✅ user_id: "test_integration"
- ✅ total_memories >= 4
- ❌ 失敗: エラー、またはフィールド不足

---

### Test 3.10: Memory Lifecycle - 圧縮

**実行コマンド**:
```bash
curl -s -X POST 'http://localhost:8000/api/v1/memory/lifecycle/compress?user_id=test_integration' | jq
```

**期待される出力**:
```json
{
  "user_id": "test_integration",
  "compressed_count": X,
  "compression_ratio": X.XX,
  ...
}
```

**判定基準**:
- ✅ HTTPステータス: 200
- ✅ user_id: "test_integration"
- ✅ compressed_count フィールドが存在
- ❌ 失敗: エラー

---

### Test 3.11: Memory Lifecycle - 期限切れクリーンアップ

**実行コマンド**:
```bash
curl -s -X DELETE 'http://localhost:8000/api/v1/memory/lifecycle/cleanup-expired' | jq
```

**期待される出力**:
```json
{
  "deleted_count": 1
}
```

**判定基準**:
- ✅ HTTPステータス: 200
- ✅ deleted_count >= 0
- ❌ 失敗: エラー

---

### Test 3.12: Dashboard Analytics - システム概要

**実行コマンド**:
```bash
curl -s -X GET 'http://localhost:8000/api/v1/dashboard/overview' | jq
```

**期待される出力**:
```json
{
  "total_intents": X,
  "total_corrections": X,
  "total_contradictions": X,
  ...
}
```

**判定基準**:
- ✅ HTTPステータス: 200
- ✅ 各フィールドが数値
- ❌ 失敗: エラー、またはフィールド不足

---

### Test 3.13: Dashboard Analytics - タイムライン

**実行コマンド**:
```bash
curl -s -X GET 'http://localhost:8000/api/v1/dashboard/timeline?granularity=day' | jq
```

**期待される出力**:
```json
{
  "timeline": [
    {
      "timestamp": "2025-12-02T00:00:00Z",
      "intents_count": X,
      "corrections_count": X,
      ...
    }
  ]
}
```

**判定基準**:
- ✅ HTTPステータス: 200
- ✅ timeline が配列
- ❌ 失敗: エラー、またはフォーマット違い

---

### Test 3.14: Dashboard Analytics - 修正履歴

**実行コマンド**:
```bash
curl -s -X GET 'http://localhost:8000/api/v1/dashboard/corrections?limit=10' | jq
```

**期待される出力**:
```json
{
  "corrections": [
    {
      "id": "...",
      "intent_id": "...",
      "source": "YUNO",
      ...
    }
  ],
  "count": X
}
```

**判定基準**:
- ✅ HTTPステータス: 200
- ✅ corrections が配列
- ✅ count >= 0
- ❌ 失敗: エラー

---

### 📊 Phase 3 報告テンプレート

```markdown
## Phase 3: API実行テスト - 完了報告

| Test | エンドポイント | HTTPステータス | 判定 | 備考 |
|------|--------------|---------------|------|------|
| 3.1  | GET /contradiction/pending | [200/エラー] | ✅/❌ | count=X (期待=1) |
| 3.2  | POST /contradiction/check | [200/エラー] | ✅/❌ | count=X (期待>=1) |
| 3.3  | PUT /contradiction/{id}/resolve | [200/エラー] | ✅/❌ | status=resolved |
| 3.4  | POST /intent/reeval | [200/エラー] | ✅/❌ | - |
| 3.5  | GET /choice-points/pending | [200/エラー] | ✅/❌ | count=X (期待>=1) |
| 3.6  | POST /choice-points/ | [200/エラー] | ✅/❌ | id=[記録] |
| 3.7  | PUT /choice-points/{id}/decide | [200/エラー] | ✅/❌ | selected=A |
| 3.8  | GET /choice-points/search | [200/エラー] | ✅/❌ | count=X |
| 3.9  | GET /lifecycle/status | [200/エラー] | ✅/❌ | total>=4 |
| 3.10 | POST /lifecycle/compress | [200/エラー] | ✅/❌ | - |
| 3.11 | DELETE /lifecycle/cleanup-expired | [200/エラー] | ✅/❌ | deleted>=0 |
| 3.12 | GET /dashboard/overview | [200/エラー] | ✅/❌ | - |
| 3.13 | GET /dashboard/timeline | [200/エラー] | ✅/❌ | - |
| 3.14 | GET /dashboard/corrections | [200/エラー] | ✅/❌ | - |

**成功**: X/14
**失敗**: X/14

[失敗したテストがある場合は、エラー内容を詳細に記載]

**Phase 3 総合判定**: ✅全成功 / ❌一部失敗

[失敗がある場合は停止]
```

---

## Phase 4: E2Eフローテスト（10分）

### 目的
複数のAPIを連携させた実際の使用シナリオを確認する。

### E2E Test 1: 矛盾検出→解決フロー

**シナリオ**: 新しいIntentの矛盾を検出し、解決するまでの一連の流れ

**Step 4.1.1**: 矛盾チェック

**実行コマンド**:
```bash
curl -s -X POST 'http://localhost:8000/api/v1/contradiction/check' \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_integration",
    "intent_id": "44444444-4444-4444-4444-444444444444",
    "intent_content": "データベースをMongoDBに変更"
  }' | jq
```

**期待される結果**:
- ✅ count >= 1（矛盾が検出される）
- ✅ contradiction_type: "TECH_STACK"

**Step 4.1.2**: 検出された矛盾のIDを記録

**実行コマンド**:
```bash
# 上記のレスポンスから contradictions[0].id を取得
```

**Step 4.1.3**: 矛盾を解決

**実行コマンド**:
```bash
# ⚠️ {contradiction_id} を Step 4.1.2 で取得したIDに置き換える
curl -s -X PUT 'http://localhost:8000/api/v1/contradiction/{contradiction_id}/resolve' \
  -H "Content-Type: application/json" \
  -d '{
    "resolution_action": "mistake",
    "resolution_rationale": "MongoDB採用は誤り、PostgreSQLを継続",
    "resolved_by": "test_integration"
  }' | jq
```

**期待される結果**:
- ✅ HTTPステータス: 200
- ✅ status: "resolved"

**Step 4.1.4**: 解決後の確認（未解決矛盾が減っているか）

**実行コマンド**:
```bash
curl -s -X GET 'http://localhost:8000/api/v1/contradiction/pending?user_id=test_integration' | jq '.count'
```

**期待される結果**:
- ✅ count が Phase 3 の Test 3.1 より少ない

---

### E2E Test 2: Choice Preservation→検索フロー

**シナリオ**: 選択肢を作成→決定→後で検索して振り返る

**Step 4.2.1**: 新しい選択肢を作成

**実行コマンド**:
```bash
curl -s -X POST 'http://localhost:8000/api/v1/memory/choice-points/' \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_integration",
    "question": "キャッシュ戦略の選定",
    "choices": [
      {"choice_id": "A", "choice_text": "Redis"},
      {"choice_id": "B", "choice_text": "Memcached"},
      {"choice_id": "C", "choice_text": "PostgreSQL cache"}
    ],
    "tags": ["e2e-test", "caching", "performance"],
    "context_type": "technical"
  }' | jq '.choice_point.id' -r
```

**期待される結果**:
- ✅ choice_point.id が返る（記録する）

**Step 4.2.2**: 選択を決定

**実行コマンド**:
```bash
# ⚠️ {choice_point_id} を Step 4.2.1 で取得したIDに置き換える
curl -s -X PUT 'http://localhost:8000/api/v1/memory/choice-points/{choice_point_id}/decide' \
  -H "Content-Type: application/json" \
  -d '{
    "selected_choice_id": "A",
    "decision_rationale": "Redisは高速で実績豊富",
    "rejection_reasons": {
      "B": "機能が限定的",
      "C": "パフォーマンスが不十分"
    }
  }' | jq
```

**期待される結果**:
- ✅ HTTPステータス: 200
- ✅ selected_choice_id: "A"

**Step 4.2.3**: タグで検索

**実行コマンド**:
```bash
curl -s -X GET 'http://localhost:8000/api/v1/memory/choice-points/search?user_id=test_integration&tags=e2e-test' | jq
```

**期待される結果**:
- ✅ results 配列に Step 4.2.1 で作成した choice_point が含まれる
- ✅ selected_choice_id: "A"
- ✅ decision_rationale が一致

**Step 4.2.4**: フルテキスト検索

**実行コマンド**:
```bash
curl -s -X GET 'http://localhost:8000/api/v1/memory/choice-points/search?user_id=test_integration&search_text=キャッシュ' | jq
```

**期待される結果**:
- ✅ results に "キャッシュ戦略の選定" が含まれる

---

### 📊 Phase 4 報告テンプレート

```markdown
## Phase 4: E2Eフローテスト - 完了報告

### E2E Test 1: 矛盾検出→解決フロー

**Step 4.1.1**: 矛盾チェック
- 判定: ✅成功 / ❌失敗
- count: X (期待>=1)

**Step 4.1.2**: 矛盾ID記録
- contradiction_id: [ここに記録]

**Step 4.1.3**: 矛盾解決
- 判定: ✅成功 / ❌失敗
- status: [resolved/その他]

**Step 4.1.4**: 解決後の確認
- 判定: ✅成功 / ❌失敗
- count: X (前回より減少: ✅/❌)

---

### E2E Test 2: Choice Preservation→検索フロー

**Step 4.2.1**: 選択肢作成
- 判定: ✅成功 / ❌失敗
- choice_point_id: [ここに記録]

**Step 4.2.2**: 選択決定
- 判定: ✅成功 / ❌失敗
- selected_choice_id: [A/その他]

**Step 4.2.3**: タグ検索
- 判定: ✅成功 / ❌失敗
- 作成した choice_point が見つかった: ✅/❌

**Step 4.2.4**: フルテキスト検索
- 判定: ✅成功 / ❌失敗
- "キャッシュ戦略の選定" が見つかった: ✅/❌

**Phase 4 総合判定**: ✅全成功 / ❌一部失敗

[失敗がある場合は停止]
```

---

## Phase 5: 最終確認と報告（5分）

### 目的
全テストの結果をまとめ、総合的な判定を行う。

### Step 5.1: テスト結果サマリー

**実行コマンド**:
```bash
echo "=== Backend API統合テスト 最終結果 ===" && \
echo "" && \
echo "Phase 0: 事前確認" && \
echo "Phase 1: Docker環境構築" && \
echo "Phase 2: テストデータ投入" && \
echo "Phase 3: API実行テスト (14件)" && \
echo "Phase 4: E2Eフローテスト (2件)" && \
echo "" && \
echo "総合判定: [ここに手動で記入]"
```

---

### 📊 Phase 5 最終報告テンプレート

```markdown
## Backend API統合テスト - 最終報告

**実行日時**: 2025-12-02 [HH:MM]  
**実行者**: Kiro (Claude Sonnet 4.5)  
**所要時間**: X分

---

### Phase別結果

| Phase | 内容 | 結果 | 備考 |
|-------|------|------|------|
| Phase 0 | 事前確認 (3ステップ) | ✅/❌ | [問題があれば記載] |
| Phase 1 | Docker環境構築 (5ステップ) | ✅/❌ | [問題があれば記載] |
| Phase 2 | テストデータ投入 (3ステップ) | ✅/❌ | [問題があれば記載] |
| Phase 3 | API実行テスト (14件) | X/14成功 | [失敗があれば記載] |
| Phase 4 | E2Eフローテスト (2件) | X/2成功 | [失敗があれば記載] |

---

### エンドポイント別結果

#### ✅ 成功したエンドポイント (X件)
- [リストアップ]

#### ❌ 失敗したエンドポイント (X件)
- [リストアップ + エラー内容]

---

### 総合判定

**結果**: ✅全合格 / ⚠️部分合格 / ❌不合格

**判定基準**:
- ✅ 全合格: Phase 3 (14/14) + Phase 4 (2/2) = 16/16
- ⚠️ 部分合格: 12/16以上
- ❌ 不合格: 12/16未満

---

### 推奨事項

[失敗があった場合、次に何をすべきかを記載]

1. [推奨事項1]
2. [推奨事項2]
...

---

### 添付ファイル

[必要に応じて、エラーログや実行結果の詳細ファイルを記載]
```

---

## 補足: エラー発生時の対応

### よくあるエラーと対処法

#### エラー1: "Connection refused" (curl実行時)

**原因**: Backend APIが起動していない

**対処法**:
```bash
# ログ確認
docker logs resonant_backend --tail 50

# コンテナ再起動
docker compose restart backend
```

**報告内容**: エラーログを全文コピーして報告

---

#### エラー2: "column does not exist" (PostgreSQL)

**原因**: スキーマが最新でない

**対処法**:
```bash
# スキーマを確認
docker exec resonant_postgres psql -U resonant -d resonant_dashboard -c "\d contradictions"
```

**報告内容**: 実際のスキーマ定義を報告

---

#### エラー3: "404 Not Found" (API実行時)

**原因**: ルーターが登録されていない、またはURL誤り

**対処法**:
```bash
# 登録されているルートを確認
curl -s http://localhost:8000/docs | grep -o '"url":"[^"]*"'
```

**報告内容**: 利用可能なエンドポイント一覧を報告

---

#### エラー4: "500 Internal Server Error"

**原因**: Backend API内部エラー

**対処法**:
```bash
# Backend APIログを確認
docker logs resonant_backend --tail 100
```

**報告内容**: エラースタックトレースを全文コピーして報告

---

## 重要: 最後のチェックリスト

テスト完了後、以下を確認してください：

- [ ] Phase 0-5 すべての報告テンプレートを埋めた
- [ ] 各APIエンドポイントの実際の出力をコピーした（要約せず全文）
- [ ] エラーが出た場合、エラーメッセージを全文コピーした
- [ ] 成功/失敗の判定を明確に記載した
- [ ] 次に何をすべきかを理解している
- [ ] この仕様書に記載されていないコマンドを実行していない
- [ ] ファイルを勝手に編集していない

---

**作成日**: 2025-12-02  
**作成者**: Kana (Claude Sonnet 4.5)  
**対象**: Kiro (Claude Sonnet 4.5 via Cursor)  
**バージョン**: 1.0.0  
**想定時間**: 60分
