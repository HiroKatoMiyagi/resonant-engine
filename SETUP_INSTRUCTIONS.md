# Docker開発環境セットアップ完了報告

## ✅ 完了したタスク

### 1. Sprint 1以降のスキーマ変更を調査 ✅
- Sprint 1: 基本スキーマ (messages, intents, specifications, notifications)
- Sprint 4: Intent/Message NOTIFY triggers
- Sprint 4.5: Claude Code tables
- **Sprint 3-7: Memory System** ← 追加が必要だった

### 2. Docker環境の現状を確認 ✅
**既存構成**:
- `docker/docker-compose.yml`: 完全版（5サービス）
- `docker/postgres/*.sql`: 初期化SQLファイル（01-04）
- **欠けていたもの**: Memory Systemスキーマ

### 3. Memory Systemスキーマ(005)を作成 ✅
**新規作成**: `docker/postgres/005_memory_system.sql`

含まれる内容:
- pgvector拡張の有効化
- **memories**テーブル（1536次元ベクトル、Sprint 3）
- **sessions**テーブル（Sprint 7）
- messagesテーブル拡張（role, session_id追加）
- intentsテーブル拡張（user_id, session_id追加）
- Full-text search (tsvector)
- メモリクリーンアップ関数

### 4. docker-compose.ymlを更新 ✅
**変更内容**:
```yaml
# Before
image: postgres:15-alpine

# After
image: ankane/pgvector:v0.5.1  # PostgreSQL 15 + pgvector
```

**追加**:
```yaml
volumes:
  - ./postgres/005_memory_system.sql:/docker-entrypoint-initdb.d/05_memory_system.sql:ro
```

### 5. 統合セットアップスクリプトを作成 ✅
**新規作成**: `setup_docker_dev.sh`

機能:
- 環境変数の確認・設定
- Docker環境のクリーンアップ（オプション）
- PostgreSQL + pgvectorの起動
- スキーマの自動検証
- 開発用環境変数ファイル（.env.docker）の生成
- ヘルスチェック

### 6. ドキュメント作成 ✅
**新規作成**: `DOCKER_SETUP.md`

内容:
- クイックスタートガイド
- Docker環境の構成説明
- よく使うコマンド集
- トラブルシューティング
- スキーマ詳細

---

## 🚀 ローカル環境での実行手順（macOS）

### ステップ1: リポジトリの同期

```bash
# ブランチを確認
cd /Users/zero/Projects/resonant-engine
git status

# 最新の変更を取得（このブランチの変更が含まれる）
git pull origin claude/sync-postgres-schema-01Ux8VUZ5ZQctviEHbAHzDn3
```

### ステップ2: セットアップスクリプトの実行

```bash
# プロジェクトルートで実行
./setup_docker_dev.sh
```

スクリプトが実行すること:
1. ✅ Docker/Docker Composeの確認
2. ✅ `.env`ファイルの確認・作成
3. ⚠️ **POSTGRES_PASSWORD**の設定確認 → 未設定なら手動編集を促す
4. クリーンアップオプション（既存データ削除するか確認）
5. Docker環境の起動（PostgreSQL + pgvector）
6. スキーマの自動検証（テーブル数、pgvector有効化確認）
7. `.env.docker`の生成

### ステップ3: 環境変数の設定（初回のみ）

スクリプトが`.env`ファイルの編集を促した場合:

```bash
vi docker/.env
```

**必須設定**:
```bash
POSTGRES_PASSWORD=your_secure_password_123!  # 安全なパスワードに変更
ANTHROPIC_API_KEY=sk-ant-...  # ClaudeのAPIキー（テスト実行時に必要）
```

保存後、スクリプトを再実行:
```bash
./setup_docker_dev.sh
```

### ステップ4: 動作確認

```bash
# 環境変数を読み込む
source .env.docker

# Python仮想環境を有効化
cd /Users/zero/Projects/resonant-engine
source venv/bin/activate

# データベース接続確認
docker-compose -f docker/docker-compose.yml exec postgres psql -U resonant -d resonant_dashboard -c "\dt"

# 期待される出力: テーブル一覧（messages, intents, memories, sessions, etc.）
```

### ステップ5: Sprint 6テスト実行

```bash
# 環境変数を確認
echo $DATABASE_URL
# 出力: postgresql://resonant:...@localhost:5432/resonant_dashboard

# テスト実行
pytest tests/ -v

# Sprint 6専用テスト
pytest tests/context_assembler/ -v
pytest tests/intent_bridge/ -v

# 受け入れテスト
pytest tests/acceptance/ -v -m acceptance
```

---

## 📊 作成・更新されたファイル

### 新規作成
1. **docker/postgres/005_memory_system.sql** - Memory Systemスキーマ
2. **setup_docker_dev.sh** - 統合セットアップスクリプト
3. **DOCKER_SETUP.md** - Docker環境ガイド
4. **SETUP_INSTRUCTIONS.md** - この手順書
5. **docker/.env** - 環境変数ファイル（テンプレート）

### 更新
1. **docker/docker-compose.yml** - pgvectorイメージ + 005追加
2. **docker-compose.yml**（ルート） - pgvectorイメージ + 005追加

---

## 🎯 期待される結果

### データベーステーブル（確認方法）

```bash
docker-compose -f docker/docker-compose.yml exec postgres psql -U resonant -d resonant_dashboard -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;"
```

**期待されるテーブル**:
- claude_code_executions
- claude_code_sessions
- intents ← user_id, session_id追加
- memories ← 新規
- messages ← role, session_id追加
- notifications
- sessions ← 新規
- specifications

### pgvector拡張（確認方法）

```bash
docker-compose -f docker/docker-compose.yml exec postgres psql -U resonant -d resonant_dashboard -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
```

**期待される出力**:
```
 oid  | extname | extowner | extnamespace | ...
------+---------+----------+--------------+-----
 xxxxx | vector  | 10       | 2200         | ...
```

### memoriesテーブルの構造（確認方法）

```bash
docker-compose -f docker/docker-compose.yml exec postgres psql -U resonant -d resonant_dashboard -c "\d memories"
```

**期待されるカラム**:
- id (bigserial)
- content (text)
- embedding (vector(1536)) ← pgvector
- memory_type (varchar)
- source_type (varchar)
- user_id (varchar)
- session_id (varchar)
- metadata (jsonb)
- created_at (timestamp)
- expires_at (timestamp)
- is_archived (boolean)
- content_tsvector (tsvector) ← Full-text search

---

## 🐛 トラブルシューティング

### Issue 1: ポート5432が使用中

**原因**: ローカルPostgreSQLが起動している

**解決策**:
```bash
# ローカルPostgreSQLを停止
brew services stop postgresql
# または
pg_ctl stop

# 確認
lsof -i :5432
```

### Issue 2: スキーマが古い

**原因**: 既存のDockerボリュームに古いスキーマが残っている

**解決策**:
```bash
# 完全リセット
docker-compose -f docker/docker-compose.yml down -v
./setup_docker_dev.sh
```

### Issue 3: pgvectorが有効にならない

**原因**: イメージのプルに失敗している

**解決策**:
```bash
# 最新イメージを取得
docker pull ankane/pgvector:v0.5.1

# 再セットアップ
docker-compose -f docker/docker-compose.yml down -v
./setup_docker_dev.sh
```

### Issue 4: DATABASE_URLが設定されていない

**原因**: .env.dockerが読み込まれていない

**解決策**:
```bash
# 再読み込み
source .env.docker

# 確認
echo $DATABASE_URL
```

---

## 📝 次のステップ

### 1. ローカル環境でのセットアップ

```bash
cd /Users/zero/Projects/resonant-engine
./setup_docker_dev.sh
```

### 2. Sprint 6テスト実行

```bash
source .env.docker
source venv/bin/activate
pytest tests/ -v
```

### 3. 開発継続

Docker環境が**開発環境の標準**になります：
- ローカルPostgreSQLは不要
- 常にDocker環境で開発・テスト
- 本番環境（Oracle Cloud）と完全一致

### 4. gitへのコミット

セットアップ完了後、変更をコミット：

```bash
git add .
git commit -m "feat: Docker環境を完全開発環境に統一

- Memory System schema (005_memory_system.sql) 追加
- pgvectorサポート (ankane/pgvector:v0.5.1)
- 統合セットアップスクリプト (setup_docker_dev.sh)
- Docker環境ドキュメント (DOCKER_SETUP.md)
- messages/intents拡張 (role, session_id, user_id)
- memories/sessionsテーブル追加

Sprint 1-7の全スキーマを統合。
ローカルPostgreSQL不要、Docker環境のみで開発可能。"

git push origin claude/sync-postgres-schema-01Ux8VUZ5ZQctviEHbAHzDn3
```

---

**作成日**: 2025-11-19
**思想**: Docker = 開発環境 = 本番環境（Infrastructure as Code）
**目的**: Sprint 1からの設計思想を完全実装
