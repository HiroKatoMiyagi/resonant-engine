# Resonant Engine - Docker開発環境セットアップガイド

## 📋 概要

Resonant Engineの開発環境は**完全にDocker化**されています。ローカルPostgreSQLは不要です。

### なぜDocker環境？

**Sprint 1（2025-11-17）からの設計思想**:
```
Before: 宏啓 → Notion → Kana
After:  宏啓 → PostgreSQL（Docker） → Kana

目的:
1. 自前インフラで自律性を獲得
2. Infrastructure as Code で再現性を保証
3. ローカル開発 = 本番環境（Oracle Cloud）
4. 外部依存を最小化
```

## 🚀 クイックスタート

### 1. 前提条件

- Docker 20.10以上
- Docker Compose V2以上
- 5432ポートが空いていること

```bash
# 確認
docker --version
docker-compose --version
```

### 2. セットアップ（3分）

```bash
# プロジェクトルートで実行
./setup_docker_dev.sh
```

スクリプトが自動的に：
1. 環境変数ファイルの確認・作成
2. Docker環境のクリーンアップ（オプション）
3. PostgreSQL + pgvectorの起動
4. スキーマの初期化・検証
5. 開発用環境変数ファイル（.env.docker）の生成

### 3. 環境変数の設定

初回実行時、`.env`ファイルの編集が必要です：

```bash
vi docker/.env
```

**必須設定**:
```bash
POSTGRES_PASSWORD=your_secure_password_123!
ANTHROPIC_API_KEY=sk-ant-...
```

### 4. 開発開始

```bash
# 環境変数を読み込む
source .env.docker

# Python仮想環境を有効化
source venv/bin/activate

# テスト実行
pytest tests/ -v
```

## 📊 Docker環境の構成

### サービス構成（docker/docker-compose.yml）

```yaml
services:
  postgres:        # PostgreSQL 15 + pgvector
  backend:         # FastAPI (Sprint 2)
  frontend:        # React (Sprint 3)
  intent_bridge:   # Intent処理 (Sprint 4)
  message_bridge:  # Message自動応答
```

### データベーススキーマ

Docker起動時に自動実行されるSQLファイル：

1. **01_init.sql** (Sprint 1)
   - messages, specifications, intents, notifications

2. **02_intent_notify.sql** (Sprint 4)
   - Intent LISTEN/NOTIFY triggers

3. **03_message_notify.sql** (Message Response)
   - Message LISTEN/NOTIFY triggers

4. **04_claude_code_tables.sql** (Sprint 4.5)
   - claude_code_sessions, claude_code_executions

5. **05_memory_system.sql** (Sprint 3-7) ← 新規追加
   - **memories** (pgvector, Sprint 3)
   - **sessions** (Sprint 7)
   - messages拡張 (role, session_id)
   - intents拡張 (user_id, session_id)

## 🛠️ よく使うコマンド

### Docker操作

```bash
# PostgreSQLのみ起動（開発用）
cd docker
docker-compose up -d postgres

# 全サービス起動
docker-compose up -d

# ログ確認
docker-compose logs -f postgres

# 停止
docker-compose down

# 完全削除（データも削除）
docker-compose down -v
```

### データベース操作

```bash
# psqlに接続
docker-compose -f docker/docker-compose.yml exec postgres psql -U resonant -d resonant_dashboard

# テーブル一覧
\dt

# pgvector拡張の確認
\dx

# スキーマ確認
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';

# memoriesテーブルの確認
SELECT COUNT(*) FROM memories;
```

### ヘルスチェック

```bash
cd docker
./scripts/check-health.sh
```

## 🧪 テスト実行

### Sprint 6受け入れテスト

```bash
# 環境変数を読み込む
source .env.docker

# 仮想環境を有効化
source venv/bin/activate

# テスト実行
pytest tests/ -v

# Sprint 6専用
pytest tests/context_assembler/ -v
pytest tests/intent_bridge/ -v
```

## 🔧 トラブルシューティング

### ポート5432が使用中

```bash
# ローカルPostgreSQLを停止
sudo systemctl stop postgresql
# または
pg_ctl stop

# または.envでポート変更
POSTGRES_PORT=5433
```

### スキーマが古い

```bash
# 完全リセット
docker-compose down -v
./setup_docker_dev.sh
```

### pgvectorが有効にならない

```bash
# PostgreSQLに接続して確認
docker-compose exec postgres psql -U resonant -d resonant_dashboard -c "SELECT * FROM pg_extension WHERE extname = 'vector';"

# 表示されない場合
docker-compose down -v
docker-compose pull  # 最新イメージを取得
docker-compose up -d
```

### 環境変数が反映されない

```bash
# .env.dockerを再生成
./setup_docker_dev.sh

# 読み込み直し
source .env.docker
```

## 📚 スキーマ詳細

### memoriesテーブル（Sprint 3）

```sql
CREATE TABLE memories (
    id BIGSERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding vector(1536),  -- pgvector
    memory_type VARCHAR(50),  -- 'working', 'longterm'
    source_type VARCHAR(50),  -- 'intent', 'message', etc.
    user_id VARCHAR(100),
    session_id VARCHAR(255),
    metadata JSONB,
    created_at TIMESTAMP,
    expires_at TIMESTAMP,  -- Working Memory TTL
    is_archived BOOLEAN
);
```

### sessionsテーブル（Sprint 7）

```sql
CREATE TABLE sessions (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(100),
    title VARCHAR(500),
    summary TEXT,  -- AI生成サマリー
    metadata JSONB,
    created_at TIMESTAMP,
    ended_at TIMESTAMP
);
```

## 🎯 次のステップ

### 開発フロー

1. **Docker環境起動**
   ```bash
   cd docker
   docker-compose up -d postgres
   ```

2. **環境変数読み込み**
   ```bash
   source .env.docker
   ```

3. **開発・テスト**
   ```bash
   source venv/bin/activate
   pytest tests/ -v
   ```

4. **停止**
   ```bash
   docker-compose down
   ```

### Oracle Cloudデプロイ（Sprint 5）

Docker環境がそのままOracle Cloud Free TierのVMにデプロイされます：

```
ローカル開発（Docker） = 本番環境（Oracle Cloud VM + Docker）
```

月額$0で本番公開が可能です。

## 📖 関連ドキュメント

- [Sprint 1: 環境構築仕様書](docs/02_components/postgresql_dashboard/architecture/sprint1_environment_setup_spec.md)
- [Sprint 3: Memory Store仕様書](docs/02_components/memory_system/architecture/sprint3_memory_store_spec.md)
- [Sprint 5: Oracle Cloudデプロイ仕様書](docs/02_components/postgresql_dashboard/architecture/sprint5_oracle_cloud_deploy_spec.md)
- [Sprint 6: Intent Bridge統合仕様書](docs/02_components/memory_system/architecture/sprint6_intent_bridge_integration_spec.md)

---

**作成日**: 2025-11-19
**更新**: Docker環境への完全移行
**思想**: Infrastructure as Code、ローカル = 本番
