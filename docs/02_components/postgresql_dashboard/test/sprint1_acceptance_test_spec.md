# Sprint 1: Docker Compose + PostgreSQL 環境構築 受け入れテスト仕様書

**対象**: Sprint 1 環境構築
**テスト期間**: Day 3
**承認者**: 宏啓（プロジェクトオーナー）

---

## 1. テスト目的

Sprint 1の成果物が仕様通りに動作し、本番運用に耐えうる品質を持つことを確認する。

---

## 2. テストカテゴリ

### 2.1 機能テスト（Functional Tests）
### 2.2 性能テスト（Performance Tests）
### 2.3 セキュリティテスト（Security Tests）
### 2.4 永続化テスト（Persistence Tests）
### 2.5 運用テスト（Operational Tests）

---

## 3. 機能テスト

### TEST-F001: Docker Compose起動テスト

**目的**: docker-composeが正常に起動すること

**手順**:
```bash
cd /Users/zero/Projects/resonant-engine/docker
docker-compose up -d
```

**期待結果**:
- [ ] コマンドが成功（exit code 0）
- [ ] resonant_postgresコンテナが作成される
- [ ] エラーメッセージなし

**判定基準**: PASS / FAIL

---

### TEST-F002: PostgreSQL接続テスト

**目的**: PostgreSQLに接続できること

**手順**:
```bash
docker-compose exec postgres psql -U resonant -d resonant_dashboard -c "SELECT 1 as test;"
```

**期待結果**:
- [ ] 接続成功
- [ ] クエリ結果が返る（test = 1）

**判定基準**: PASS / FAIL

---

### TEST-F003: テーブル作成確認テスト

**目的**: 4つのコアテーブルが作成されていること

**手順**:
```bash
docker-compose exec postgres psql -U resonant -d resonant_dashboard -c "\dt"
```

**期待結果**:
- [ ] messages テーブルが存在
- [ ] specifications テーブルが存在
- [ ] intents テーブルが存在
- [ ] notifications テーブルが存在

**判定基準**: 4/4テーブル確認 = PASS

---

### TEST-F004: インデックス作成確認テスト

**目的**: 必要なインデックスが作成されていること

**手順**:
```bash
docker-compose exec postgres psql -U resonant -d resonant_dashboard -c "\di"
```

**期待結果**:
- [ ] idx_messages_user_id が存在
- [ ] idx_messages_created_at が存在
- [ ] idx_specifications_status が存在
- [ ] idx_specifications_tags (GIN) が存在
- [ ] idx_intents_status が存在
- [ ] idx_notifications_user_id が存在

**判定基準**: 6/6インデックス以上 = PASS

---

### TEST-F005: CRUD操作テスト - Messages

**目的**: messagesテーブルのCRUD操作が正常に動作すること

**手順**:
```sql
-- CREATE
INSERT INTO messages (user_id, content, message_type)
VALUES ('test_user', 'Test message', 'user')
RETURNING id;

-- READ
SELECT * FROM messages WHERE user_id = 'test_user';

-- UPDATE
UPDATE messages SET content = 'Updated message' WHERE user_id = 'test_user';

-- DELETE
DELETE FROM messages WHERE user_id = 'test_user';
```

**期待結果**:
- [ ] INSERT成功、UUIDが返る
- [ ] SELECT成功、データが取得できる
- [ ] UPDATE成功、1行更新
- [ ] DELETE成功、1行削除

**判定基準**: 4/4操作成功 = PASS

---

### TEST-F006: CRUD操作テスト - Specifications

**目的**: specificationsテーブルのCRUD操作が正常に動作すること

**手順**:
```sql
-- CREATE
INSERT INTO specifications (title, content, status, tags)
VALUES ('Test Spec', '# Test Content', 'draft', ARRAY['test', 'sprint1'])
RETURNING id;

-- READ with tag filter
SELECT * FROM specifications WHERE 'test' = ANY(tags);

-- UPDATE
UPDATE specifications SET status = 'review' WHERE title = 'Test Spec';

-- DELETE
DELETE FROM specifications WHERE title = 'Test Spec';
```

**期待結果**:
- [ ] INSERT成功、タグ配列が保存される
- [ ] タグフィルタリングが動作
- [ ] ステータス更新成功
- [ ] DELETE成功

**判定基準**: 4/4操作成功 = PASS

---

### TEST-F007: CRUD操作テスト - Intents

**目的**: intentsテーブルのCRUD操作が正常に動作すること

**手順**:
```sql
-- CREATE
INSERT INTO intents (description, intent_type, status, priority)
VALUES ('Test Intent', 'feature_request', 'pending', 5)
RETURNING id;

-- READ with status filter
SELECT * FROM intents WHERE status = 'pending' ORDER BY priority DESC;

-- UPDATE with JSONB
UPDATE intents
SET status = 'completed',
    result = '{"success": true, "message": "Processed"}'::jsonb,
    processed_at = NOW()
WHERE description = 'Test Intent';

-- DELETE
DELETE FROM intents WHERE description = 'Test Intent';
```

**期待結果**:
- [ ] INSERT成功
- [ ] 優先度ソートが機能
- [ ] JSONB保存成功
- [ ] processed_at更新成功
- [ ] DELETE成功

**判定基準**: 5/5操作成功 = PASS

---

### TEST-F008: CRUD操作テスト - Notifications

**目的**: notificationsテーブルのCRUD操作が正常に動作すること

**手順**:
```sql
-- CREATE
INSERT INTO notifications (user_id, title, message, notification_type)
VALUES ('test_user', 'Test Notification', 'Test message', 'info')
RETURNING id;

-- READ unread
SELECT * FROM notifications WHERE user_id = 'test_user' AND is_read = FALSE;

-- UPDATE (mark as read)
UPDATE notifications SET is_read = TRUE WHERE user_id = 'test_user';

-- DELETE
DELETE FROM notifications WHERE user_id = 'test_user';
```

**期待結果**:
- [ ] INSERT成功
- [ ] 未読フィルタリング動作
- [ ] 既読更新成功
- [ ] DELETE成功

**判定基準**: 4/4操作成功 = PASS

---

### TEST-F009: ヘルスチェックスクリプトテスト

**目的**: check-health.shが正常に動作すること

**手順**:
```bash
./scripts/check-health.sh
```

**期待結果**:
- [ ] Docker確認: PASS
- [ ] PostgreSQL: HEALTHY
- [ ] Database Connection: OK
- [ ] Tables Created: 4
- [ ] 最終結果: "All health checks passed!"

**判定基準**: 全チェックPASS = PASS

---

### TEST-F010: 起動スクリプトテスト

**目的**: start.shが正常に動作すること

**手順**:
```bash
./scripts/stop.sh
./scripts/start.sh
```

**期待結果**:
- [ ] .env存在チェック動作
- [ ] パスワード検証動作
- [ ] コンテナ起動成功
- [ ] ヘルスチェック待機成功
- [ ] 接続情報表示

**判定基準**: 全ステップ成功 = PASS

---

## 4. 性能テスト

### TEST-P001: コンテナ起動時間テスト

**目的**: コンテナ起動が30秒以内に完了すること

**手順**:
```bash
./scripts/stop.sh
time ./scripts/start.sh
```

**期待結果**:
- [ ] real < 30s

**測定値**: ____秒
**判定基準**: < 30秒 = PASS

---

### TEST-P002: 大量データ挿入テスト

**目的**: 1000件のデータ挿入が5秒以内に完了すること

**手順**:
```sql
-- メッセージ1000件挿入
INSERT INTO messages (user_id, content, message_type)
SELECT
    'user_' || generate_series,
    'Message content ' || generate_series,
    'user'
FROM generate_series(1, 1000);

-- 実行時間を確認
\timing on
```

**期待結果**:
- [ ] 1000件挿入成功
- [ ] 実行時間 < 5000ms

**測定値**: ____ms
**判定基準**: < 5秒 = PASS

---

### TEST-P003: インデックス性能テスト

**目的**: インデックスを使用した検索が高速であること

**手順**:
```sql
\timing on

-- インデックス使用クエリ
EXPLAIN ANALYZE
SELECT * FROM messages WHERE user_id = 'user_500';

-- ステータスフィルタ
EXPLAIN ANALYZE
SELECT * FROM intents WHERE status = 'pending' ORDER BY priority DESC LIMIT 10;
```

**期待結果**:
- [ ] Index Scanが使用される
- [ ] 実行時間 < 10ms

**測定値**: ____ms
**判定基準**: Index使用 & < 10ms = PASS

---

## 5. セキュリティテスト

### TEST-S001: 環境変数隠蔽テスト

**目的**: .envファイルがGit管理対象外であること

**手順**:
```bash
cat ../.gitignore | grep "docker/.env"
git status | grep ".env"
```

**期待結果**:
- [ ] .gitignoreに"docker/.env"が含まれる
- [ ] git statusに.envが表示されない

**判定基準**: 両方満たす = PASS

---

### TEST-S002: パスワード強度検証テスト

**目的**: 弱いパスワードが拒否されること

**手順**:
```bash
# .envにパスワード設定
echo "POSTGRES_PASSWORD=weak" > .env

./scripts/start.sh
```

**期待結果**:
- [ ] パスワードチェックで警告/エラーが出る（オプション）
- または
- [ ] 最低でもドキュメントに強度要件が記載されている

**判定基準**: 警告機能あり or ドキュメント記載 = PASS

---

### TEST-S003: ネットワーク分離テスト

**目的**: コンテナが専用ネットワークに隔離されていること

**手順**:
```bash
docker network inspect resonant_network
```

**期待結果**:
- [ ] resonant_networkが存在
- [ ] Driver: bridge
- [ ] resonant_postgresが接続されている

**判定基準**: 全条件満たす = PASS

---

## 6. 永続化テスト

### TEST-D001: データ永続化テスト

**目的**: コンテナ再起動後もデータが保持されること

**手順**:
```bash
# 1. データ挿入
docker-compose exec postgres psql -U resonant -d resonant_dashboard -c \
  "INSERT INTO specifications (title, content) VALUES ('Persistence Test', 'Data should persist');"

# 2. 停止
./scripts/stop.sh

# 3. 再起動
./scripts/start.sh

# 4. データ確認
docker-compose exec postgres psql -U resonant -d resonant_dashboard -c \
  "SELECT title FROM specifications WHERE title = 'Persistence Test';"
```

**期待結果**:
- [ ] データが挿入される
- [ ] 停止成功
- [ ] 再起動成功
- [ ] データが残っている

**判定基準**: データ残存 = PASS

---

### TEST-D002: ボリューム存在確認テスト

**目的**: Dockerボリュームが作成されていること

**手順**:
```bash
docker volume ls | grep resonant_postgres_data
docker volume inspect resonant_postgres_data
```

**期待結果**:
- [ ] resonant_postgres_dataボリュームが存在
- [ ] Mountpointが設定されている

**判定基準**: ボリューム存在 = PASS

---

### TEST-D003: 完全リセットテスト

**目的**: docker-compose down -vでデータが完全削除されること

**手順**:
```bash
# 1. データ挿入
docker-compose exec postgres psql -U resonant -d resonant_dashboard -c \
  "INSERT INTO messages (user_id, content) VALUES ('reset_test', 'Will be deleted');"

# 2. 完全リセット
docker-compose down -v

# 3. 再起動
./scripts/start.sh

# 4. データ確認
docker-compose exec postgres psql -U resonant -d resonant_dashboard -c \
  "SELECT * FROM messages WHERE user_id = 'reset_test';"
```

**期待結果**:
- [ ] down -vでボリューム削除
- [ ] 再起動後データが存在しない
- [ ] テーブルは再作成される

**判定基準**: データ削除 & テーブル再作成 = PASS

---

## 7. 運用テスト

### TEST-O001: ログ出力テスト

**目的**: ログが正常に出力されること

**手順**:
```bash
docker-compose logs postgres | head -20
```

**期待結果**:
- [ ] PostgreSQL起動ログが表示
- [ ] データベース作成ログが表示
- [ ] init.sql実行ログが表示
- [ ] エラーメッセージなし

**判定基準**: ログ正常 = PASS

---

### TEST-O002: README.md完成度テスト

**目的**: README.mdが必要な情報を含んでいること

**チェック項目**:
- [ ] クイックスタート手順が記載
- [ ] 前提条件が明記
- [ ] コマンド例が含まれる
- [ ] スキーマドキュメントが含まれる
- [ ] トラブルシューティングが含まれる
- [ ] 次のステップが記載

**判定基準**: 6/6項目 = PASS

---

### TEST-O003: エラーハンドリングテスト

**目的**: スクリプトが適切にエラーを処理すること

**手順**:
```bash
# .env削除時の挙動
mv .env .env.bak
./scripts/start.sh
mv .env.bak .env

# 不正なパスワード
sed -i '' 's/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=your_secure_password_here/' .env
./scripts/start.sh
```

**期待結果**:
- [ ] .env不在時に明確なエラーメッセージ
- [ ] 弱いパスワード時に警告
- [ ] スクリプトが適切に終了（exit 1）

**判定基準**: 適切なエラー処理 = PASS

---

## 8. テスト結果サマリー

### 機能テスト (10件)

| テストID | テスト名 | 結果 | 備考 |
|----------|----------|------|------|
| TEST-F001 | Docker Compose起動 | | |
| TEST-F002 | PostgreSQL接続 | | |
| TEST-F003 | テーブル作成確認 | | |
| TEST-F004 | インデックス作成確認 | | |
| TEST-F005 | CRUD - Messages | | |
| TEST-F006 | CRUD - Specifications | | |
| TEST-F007 | CRUD - Intents | | |
| TEST-F008 | CRUD - Notifications | | |
| TEST-F009 | ヘルスチェックスクリプト | | |
| TEST-F010 | 起動スクリプト | | |

### 性能テスト (3件)

| テストID | テスト名 | 測定値 | 閾値 | 結果 |
|----------|----------|--------|------|------|
| TEST-P001 | コンテナ起動時間 | ___秒 | < 30秒 | |
| TEST-P002 | 大量データ挿入 | ___ms | < 5000ms | |
| TEST-P003 | インデックス性能 | ___ms | < 10ms | |

### セキュリティテスト (3件)

| テストID | テスト名 | 結果 | 備考 |
|----------|----------|------|------|
| TEST-S001 | 環境変数隠蔽 | | |
| TEST-S002 | パスワード強度検証 | | |
| TEST-S003 | ネットワーク分離 | | |

### 永続化テスト (3件)

| テストID | テスト名 | 結果 | 備考 |
|----------|----------|------|------|
| TEST-D001 | データ永続化 | | |
| TEST-D002 | ボリューム存在確認 | | |
| TEST-D003 | 完全リセット | | |

### 運用テスト (3件)

| テストID | テスト名 | 結果 | 備考 |
|----------|----------|------|------|
| TEST-O001 | ログ出力 | | |
| TEST-O002 | README.md完成度 | | |
| TEST-O003 | エラーハンドリング | | |

---

## 9. 総合判定

### 判定基準

- **PASS**: 全テストPASS（22/22）
- **CONDITIONAL PASS**: 重要テストPASS、軽微な問題のみ（20/22以上）
- **FAIL**: 重要テストFAIL（20/22未満）

### 重要テスト（必須PASS）

- TEST-F001: Docker Compose起動
- TEST-F002: PostgreSQL接続
- TEST-F003: テーブル作成確認
- TEST-D001: データ永続化
- TEST-S001: 環境変数隠蔽
- TEST-O002: README.md完成度

### 最終判定

**テスト結果**: ___/22 PASS

**判定**: PASS / CONDITIONAL PASS / FAIL

**承認者サイン**: ____________________

**日付**: ____________________

---

## 10. 備考・改善点

（テスト実施時に発見された問題点や改善提案を記載）

---

**作成日**: 2025-11-17
**作成者**: Kana（外界翻訳層 / Claude Sonnet 4.5）
**テスト担当**: Tsumu (Cursor) または指定担当者
**承認者**: 宏啓（プロジェクトオーナー）
