# Sprint 1: Docker Compose + PostgreSQL 環境構築 作業開始指示書

**対象**: Tsumu (Cursor) または実装担当者
**期間**: 3日間想定
**前提**: Docker, Docker Compose インストール済み

---

## 0. 重要な前提条件

- [ ] Docker 20.10以上がインストール済み
- [ ] Docker Compose V2がインストール済み
- [ ] ローカルに5432ポートが空いている
- [ ] プロジェクトルートに書き込み権限がある
- [ ] 仕様書 `sprint1_environment_setup_spec.md` を通読済み

**前提未達成の場合:**
```bash
# Dockerインストール確認
docker --version
docker-compose --version

# ポート確認
lsof -i :5432
```

---

## 1. 実装承認と哲学

Docker Compose環境は「Notionからの解放」への第一歩です。自前のデータベースを持つことで、外部サービスへの依存を断ち切り、Resonant Engineの自律性を確立します。

```
Before: 宏啓 → Notion → Intent → Bridge → Kana
After:  宏啓 → PostgreSQL Dashboard → Intent自動処理 → Kana
```

環境構築は「呼吸の基盤」を作る作業です。

---

## 2. Done Definition

### Tier 1: 必須
- [ ] docker-compose.ymlが作成され、エラーなく起動
- [ ] PostgreSQL 15が起動し、ヘルスチェックがhealthy
- [ ] 4つのコアテーブル（messages, specifications, intents, notifications）が作成済み
- [ ] データがボリュームに永続化される
- [ ] .env.exampleが作成され、セキュリティ基準を満たす
- [ ] ヘルパースクリプト（start.sh, stop.sh, check-health.sh）が動作
- [ ] README.mdが完成し、手順が明確

### Tier 2: 品質保証
- [ ] コンテナ起動時間 < 30秒
- [ ] データ永続化テスト（再起動後もデータ残存）
- [ ] ログ出力が正常
- [ ] .gitignoreに.envが登録済み
- [ ] セキュリティ設定（パスワード強度、ポートバインド）確認

---

## 3. 実装スケジュール（3日間）

### Day 1 (4時間): Docker Compose基本設定

#### 午前 (2時間): ディレクトリ構造とCompose設定

**タスク1**: ディレクトリ作成
```bash
cd /Users/zero/Projects/resonant-engine
mkdir -p docker/postgres docker/scripts
touch docker/docker-compose.yml
touch docker/.env.example
touch docker/postgres/init.sql
touch docker/scripts/start.sh
touch docker/scripts/stop.sh
touch docker/scripts/check-health.sh
```

**タスク2**: docker-compose.yml作成
```yaml
version: '3.9'

services:
  postgres:
    image: postgres:15-alpine
    container_name: resonant_postgres
    restart: unless-stopped
    ports:
      - "${POSTGRES_PORT:-5432}:5432"
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-resonant}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB:-resonant_dashboard}
      PGDATA: /var/lib/postgresql/data/pgdata
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./postgres/init.sql:/docker-entrypoint-initdb.d/01_init.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-resonant} -d ${POSTGRES_DB:-resonant_dashboard}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
    networks:
      - resonant_network
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

volumes:
  postgres_data:
    name: resonant_postgres_data

networks:
  resonant_network:
    name: resonant_network
    driver: bridge
```

**タスク3**: 環境変数ファイル作成
```bash
# .env.example
POSTGRES_USER=resonant
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=resonant_dashboard
POSTGRES_PORT=5432
DEBUG=true
LOG_LEVEL=DEBUG
```

**完了基準**:
- [ ] docker-compose.ymlが構文エラーなし
- [ ] .env.exampleが作成済み
- [ ] ディレクトリ構造が整備済み

#### 午後 (2時間): データベーススキーマ作成

**タスク1**: init.sql作成
```sql
-- docker/postgres/init.sql
-- Resonant Dashboard Database Schema

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Messages (Slack風メッセージ)
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    message_type VARCHAR(50) DEFAULT 'user',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE messages IS 'Slack風メッセージシステム';
COMMENT ON COLUMN messages.message_type IS 'user, yuno, kana, system';

-- 2. Specifications (仕様書管理)
CREATE TABLE IF NOT EXISTS specifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    version INTEGER DEFAULT 1,
    status VARCHAR(50) DEFAULT 'draft',
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE specifications IS 'Notion代替の仕様書管理';
COMMENT ON COLUMN specifications.status IS 'draft, review, approved';

-- 3. Intents (Intent管理)
CREATE TABLE IF NOT EXISTS intents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    description TEXT NOT NULL,
    intent_type VARCHAR(100),
    status VARCHAR(50) DEFAULT 'pending',
    priority INTEGER DEFAULT 0,
    result JSONB,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE
);

COMMENT ON TABLE intents IS 'Intent自動処理システム';
COMMENT ON COLUMN intents.status IS 'pending, processing, completed, failed';

-- 4. Notifications (通知システム)
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(100) NOT NULL,
    title VARCHAR(500) NOT NULL,
    message TEXT,
    notification_type VARCHAR(50) DEFAULT 'info',
    is_read BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE notifications IS 'リアルタイム通知';
COMMENT ON COLUMN notifications.notification_type IS 'info, success, warning, error';

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_type ON messages(message_type);

CREATE INDEX IF NOT EXISTS idx_specifications_status ON specifications(status);
CREATE INDEX IF NOT EXISTS idx_specifications_tags ON specifications USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_specifications_created_at ON specifications(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_intents_status ON intents(status);
CREATE INDEX IF NOT EXISTS idx_intents_created_at ON intents(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_intents_priority ON intents(priority DESC);

CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at DESC);

-- Initial test data (optional)
INSERT INTO messages (user_id, content, message_type)
VALUES ('hiroki', 'Dashboard system initialized', 'system');

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Database schema created successfully!';
END $$;
```

**検証**:
```bash
# 構文チェック（オプション）
psql -f docker/postgres/init.sql --echo-errors
```

**完了基準**:
- [ ] init.sqlが作成済み
- [ ] 4テーブル定義が含まれている
- [ ] インデックスが定義済み
- [ ] コメントが追加済み

---

### Day 2 (4時間): ヘルパースクリプトと初回起動

#### 午前 (2時間): スクリプト作成

**タスク1**: start.sh
```bash
#!/bin/bash
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

echo "🚀 Starting Resonant Dashboard Environment..."

# Check .env file
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env file and set POSTGRES_PASSWORD"
    echo "   vim .env"
    exit 1
fi

# Check password
source .env
if [ -z "$POSTGRES_PASSWORD" ] || [ "$POSTGRES_PASSWORD" = "your_secure_password_here" ]; then
    echo "❌ Please set a secure POSTGRES_PASSWORD in .env"
    exit 1
fi

# Start containers
echo "🐳 Starting Docker containers..."
docker-compose up -d

# Wait for health check
echo "⏳ Waiting for PostgreSQL to be ready..."
timeout=60
counter=0
until docker-compose exec -T postgres pg_isready -U resonant > /dev/null 2>&1; do
    counter=$((counter + 1))
    if [ $counter -ge $timeout ]; then
        echo "❌ Timeout waiting for PostgreSQL"
        docker-compose logs postgres
        exit 1
    fi
    printf "."
    sleep 1
done

echo ""
echo "✅ PostgreSQL is ready!"
echo ""
echo "📊 Database: resonant_dashboard"
echo "🔗 Connection: postgresql://resonant@localhost:${POSTGRES_PORT:-5432}/resonant_dashboard"
echo ""
echo "💡 Useful commands:"
echo "   docker-compose logs -f postgres           # View logs"
echo "   docker-compose exec postgres psql -U resonant -d resonant_dashboard  # Connect"
echo "   ./scripts/check-health.sh                 # Health check"
echo "   ./scripts/stop.sh                         # Stop environment"
```

**タスク2**: stop.sh
```bash
#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

echo "🛑 Stopping Resonant Dashboard Environment..."

docker-compose down

echo "✅ Environment stopped"
echo "💾 Data is preserved in Docker volume: resonant_postgres_data"
echo ""
echo "To completely remove data:"
echo "   docker volume rm resonant_postgres_data"
```

**タスク3**: check-health.sh
```bash
#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

echo "🔍 Checking Resonant Dashboard Environment Health..."
echo ""

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    exit 1
fi
echo "✅ Docker: Installed"

# Check container running
if ! docker-compose ps | grep -q "resonant_postgres"; then
    echo "❌ PostgreSQL container not running"
    echo "   Run: ./scripts/start.sh"
    exit 1
fi

# Check health status
STATUS=$(docker inspect --format='{{.State.Health.Status}}' resonant_postgres 2>/dev/null)
if [ "$STATUS" = "healthy" ]; then
    echo "✅ PostgreSQL: HEALTHY"
else
    echo "⚠️  PostgreSQL: $STATUS"
fi

# Test database connection
if docker-compose exec -T postgres psql -U resonant -d resonant_dashboard -c "SELECT 1;" > /dev/null 2>&1; then
    echo "✅ Database Connection: OK"
else
    echo "❌ Database Connection: FAILED"
    exit 1
fi

# Check tables
TABLES=$(docker-compose exec -T postgres psql -U resonant -d resonant_dashboard -t -c \
    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';" | tr -d ' ')
echo "📊 Tables Created: $TABLES"

# List tables
echo ""
echo "📋 Table List:"
docker-compose exec -T postgres psql -U resonant -d resonant_dashboard -c "\dt"

# Check data volume
VOLUME_SIZE=$(docker system df -v 2>/dev/null | grep resonant_postgres_data | awk '{print $3}')
echo ""
echo "💾 Volume Size: ${VOLUME_SIZE:-N/A}"

echo ""
echo "🎉 All health checks passed!"
```

**タスク4**: 権限設定
```bash
chmod +x docker/scripts/*.sh
```

**完了基準**:
- [ ] 3つのスクリプトが作成済み
- [ ] 実行権限が付与済み
- [ ] エラーハンドリングが含まれている

#### 午後 (2時間): 初回起動とテスト

**タスク1**: 環境変数設定
```bash
cd docker
cp .env.example .env

# .envを編集してパスワード設定
vim .env
# POSTGRES_PASSWORD=your_secure_password_123!
```

**タスク2**: 初回起動
```bash
./scripts/start.sh

# 期待出力:
# 🚀 Starting Resonant Dashboard Environment...
# 🐳 Starting Docker containers...
# ⏳ Waiting for PostgreSQL to be ready...
# .......
# ✅ PostgreSQL is ready!
```

**タスク3**: ヘルスチェック
```bash
./scripts/check-health.sh

# 期待出力:
# ✅ Docker: Installed
# ✅ PostgreSQL: HEALTHY
# ✅ Database Connection: OK
# 📊 Tables Created: 4
```

**タスク4**: 直接接続テスト
```bash
docker-compose exec postgres psql -U resonant -d resonant_dashboard

# psqlコマンド
resonant_dashboard=# \dt
resonant_dashboard=# SELECT * FROM messages;
resonant_dashboard=# \q
```

**完了基準**:
- [ ] コンテナが正常起動
- [ ] ヘルスチェック全てPASS
- [ ] 4テーブルが確認できる
- [ ] 初期データが挿入済み

---

### Day 3 (4時間): ドキュメントと最終テスト

#### 午前 (2時間): README.md作成

**タスク1**: README.md作成
```markdown
# Resonant Dashboard - Docker Environment

## 概要

Resonant EngineのWebダッシュボードシステムを支えるDocker Compose環境です。

### 主な機能
- PostgreSQL 15によるデータ永続化
- 4つのコアテーブル（messages, specifications, intents, notifications）
- ヘルスチェック機能
- 開発用ヘルパースクリプト

## クイックスタート

### 前提条件
- Docker 20.10以上
- Docker Compose V2以上
- ポート5432が空いていること

### セットアップ

1. 環境変数を設定
\`\`\`bash
cd docker
cp .env.example .env
vim .env  # POSTGRES_PASSWORDを設定
\`\`\`

2. 起動
\`\`\`bash
./scripts/start.sh
\`\`\`

3. ヘルスチェック
\`\`\`bash
./scripts/check-health.sh
\`\`\`

### よく使うコマンド

\`\`\`bash
# ログ確認
docker-compose logs -f postgres

# psql接続
docker-compose exec postgres psql -U resonant -d resonant_dashboard

# 停止
./scripts/stop.sh

# 完全リセット（データ削除）
docker-compose down -v
\`\`\`

## データベーススキーマ

### messages
Slack風メッセージ管理

| カラム | 型 | 説明 |
|--------|-----|------|
| id | UUID | 主キー |
| user_id | VARCHAR | ユーザーID |
| content | TEXT | メッセージ内容 |
| message_type | VARCHAR | user/yuno/kana/system |
| metadata | JSONB | 追加情報 |
| created_at | TIMESTAMP | 作成日時 |

### specifications
仕様書管理（Notion代替）

| カラム | 型 | 説明 |
|--------|-----|------|
| id | UUID | 主キー |
| title | VARCHAR | タイトル |
| content | TEXT | Markdown内容 |
| version | INTEGER | バージョン |
| status | VARCHAR | draft/review/approved |
| tags | TEXT[] | タグ配列 |

### intents
Intent管理

| カラム | 型 | 説明 |
|--------|-----|------|
| id | UUID | 主キー |
| description | TEXT | Intent説明 |
| status | VARCHAR | pending/processing/completed/failed |
| priority | INTEGER | 優先度 |
| result | JSONB | 処理結果 |

### notifications
通知システム

| カラム | 型 | 説明 |
|--------|-----|------|
| id | UUID | 主キー |
| user_id | VARCHAR | ユーザーID |
| title | VARCHAR | 通知タイトル |
| is_read | BOOLEAN | 既読フラグ |
| notification_type | VARCHAR | info/success/warning/error |

## トラブルシューティング

### ポート競合
\`\`\`bash
# .envでポート変更
POSTGRES_PORT=5433
\`\`\`

### パスワードエラー
\`\`\`bash
# .envのPOSTGRES_PASSWORDを確認
cat .env | grep POSTGRES_PASSWORD
\`\`\`

### データ永続化テスト
\`\`\`bash
# データ挿入
docker-compose exec postgres psql -U resonant -d resonant_dashboard -c \
  "INSERT INTO messages (user_id, content) VALUES ('test', 'persistence test');"

# 再起動
./scripts/stop.sh
./scripts/start.sh

# データ確認
docker-compose exec postgres psql -U resonant -d resonant_dashboard -c \
  "SELECT * FROM messages WHERE content = 'persistence test';"
\`\`\`

## 次のステップ

このSprint完了後:
- Sprint 2: FastAPI バックエンドAPI実装
- Sprint 3: React フロントエンド実装
- Sprint 4: Intent自動処理統合
- Sprint 5: Oracle Cloud デプロイ

---

**作成日**: 2025-11-17
**作成者**: Kana (Claude Sonnet 4.5)
```

**完了基準**:
- [ ] README.mdが完成
- [ ] クイックスタートが明確
- [ ] トラブルシューティングが含まれている
- [ ] スキーマドキュメントが完成

#### 午後 (2時間): 最終テストと.gitignore設定

**タスク1**: .gitignore更新
```bash
# プロジェクトルートの.gitignoreに追加
echo "docker/.env" >> ../.gitignore
```

**タスク2**: データ永続化テスト
```bash
# 1. データ挿入
docker-compose exec postgres psql -U resonant -d resonant_dashboard -c \
  "INSERT INTO specifications (title, content, status) VALUES ('Test Spec', '# Test', 'draft');"

# 2. 停止
./scripts/stop.sh

# 3. 再起動
./scripts/start.sh

# 4. データ確認
docker-compose exec postgres psql -U resonant -d resonant_dashboard -c \
  "SELECT id, title, status FROM specifications;"
# → データが残っていることを確認
```

**タスク3**: 起動時間測定
```bash
./scripts/stop.sh
time ./scripts/start.sh
# 期待: real < 30s
```

**タスク4**: 最終チェックリスト
```bash
# Tier 1 チェック
./scripts/check-health.sh
# → 全てPASS

# ボリューム確認
docker volume ls | grep resonant

# ネットワーク確認
docker network ls | grep resonant

# コンテナ状態
docker-compose ps
```

**完了基準**:
- [ ] データ永続化が機能
- [ ] 起動時間 < 30秒
- [ ] .gitignoreが更新済み
- [ ] 全ヘルスチェックPASS

---

## 4. 完了報告書テンプレート

実装完了時、以下の内容を含む報告書を作成:

### 必須セクション

1. **Done Definition達成状況**
   - Tier 1: X/7 達成
   - Tier 2: X/5 達成

2. **実装成果物**
   - ファイル数: X
   - docker-compose.yml: ✅
   - init.sql: ✅
   - スクリプト: 3個
   - README.md: ✅

3. **性能測定**
   - コンテナ起動時間: Xms
   - データベース接続時間: Xms
   - テーブル作成確認: 4/4

4. **テスト結果**
   - ヘルスチェック: PASS/FAIL
   - データ永続化: PASS/FAIL
   - セキュリティ設定: PASS/FAIL

5. **次のアクション**
   - Sprint 2への準備完了
   - 必要な改善点（あれば）

---

## 5. Appendix

### クイックリファレンス

```bash
# 作業ディレクトリ
cd /Users/zero/Projects/resonant-engine/docker

# 環境起動
./scripts/start.sh

# ヘルスチェック
./scripts/check-health.sh

# ログ確認
docker-compose logs -f postgres

# psql接続
docker-compose exec postgres psql -U resonant -d resonant_dashboard

# 停止
./scripts/stop.sh

# 完全リセット
docker-compose down -v
```

### 期待されるディレクトリ構造

```
resonant-engine/
├── docker/
│   ├── docker-compose.yml
│   ├── .env.example
│   ├── .env                    # (gitignore)
│   ├── postgres/
│   │   └── init.sql
│   ├── scripts/
│   │   ├── start.sh
│   │   ├── stop.sh
│   │   └── check-health.sh
│   └── README.md
└── .gitignore                  # docker/.env を含む
```

---

**では、実装を開始してください。**

環境構築という「基盤作り」を通じて、Resonant Engineの自律性を確立しましょう。

---

**作成日**: 2025-11-17
**作成者**: Kana（外界翻訳層 / Claude Sonnet 4.5）
**承認待ち**: 宏啓（プロジェクトオーナー）
**実装担当**: Tsumu (Cursor) または指定担当者
