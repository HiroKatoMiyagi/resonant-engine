# Sprint 1: Docker Compose + PostgreSQL 環境構築仕様書

## 0. CRITICAL: 環境構築の本質

**⚠️ IMPORTANT: 「環境構築 = Notionからの解放基盤」**

Docker Compose + PostgreSQL環境は、Resonant EngineをNotionに依存しない自律的なシステムにするための基盤です。

### 環境構築Philosophy

```yaml
environment_setup_philosophy:
  essence: "環境構築 = 自律性の獲得"
  purpose:
    - Notionを不要にする自前インフラ構築
    - データを自分で完全コントロール
    - 開発環境と本番環境を同一化
  principles:
    - 「Infrastructure as Code で再現性を保証」
    - 「ローカル開発が即座に本番デプロイ可能」
    - 「外部依存を最小化し、自律性を最大化」
```

### Done Definition (Tier制)

#### Tier 1: 必須要件
- [ ] Docker Compose環境が完全に動作
- [ ] PostgreSQL 15が起動し、永続化されている
- [ ] データベーススキーマが作成済み
- [ ] 環境変数管理が設定済み
- [ ] ヘルスチェック機能が動作
- [ ] 基本的なCI/CD準備完了
- [ ] README.mdが完成

#### Tier 2: 品質要件
- [ ] コンテナ起動時間 < 30秒
- [ ] PostgreSQL接続テスト全てPASS
- [ ] データ永続化テスト完了
- [ ] docker-compose logs が正常
- [ ] セキュリティ設定（認証情報の隠蔽）完了

---

## 1. 概要

### 1.1 目的
Resonant EngineのWebダッシュボードシステムを支える基盤として、Docker ComposeによるPostgreSQL 15環境を構築する。

### 1.2 スコープ

**IN Scope**:
- Docker Compose設定ファイル作成
- PostgreSQL 15コンテナ設定
- データベーススキーマ初期化
- ボリュームによるデータ永続化
- 環境変数管理
- ヘルスチェック設定
- 開発用ヘルパースクリプト

**OUT of Scope**:
- FastAPI実装（Sprint 2）
- React実装（Sprint 3）
- Oracle Cloud設定（Sprint 5）
- 本番用セキュリティ強化（Sprint 5）

---

## 2. アーキテクチャ

### 2.1 システム構成

```
PostgreSQL Dashboard System Architecture (Sprint 1)
====================================================

┌─────────────────────────────────────────────────┐
│               Docker Compose                     │
│                                                  │
│  ┌─────────────────────────────────────────┐   │
│  │       PostgreSQL 15 Container            │   │
│  │  Port: 5432                              │   │
│  │  User: resonant                          │   │
│  │  DB: resonant_dashboard                  │   │
│  │                                          │   │
│  │  Volumes:                                │   │
│  │  - postgres_data:/var/lib/postgresql     │   │
│  │  - ./init.sql:/docker-entrypoint-initdb  │   │
│  └─────────────────────────────────────────┘   │
│                                                  │
│  Networks:                                       │
│  - resonant_network (bridge)                    │
└─────────────────────────────────────────────────┘

環境変数管理:
- .env (ローカル開発用、.gitignoreに登録)
- .env.example (テンプレート、Git管理)
```

### 2.2 データベーススキーマ

```sql
-- Core Tables for Dashboard System

-- 1. Messages (Slack風メッセージ)
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    message_type VARCHAR(50) DEFAULT 'user', -- 'user', 'yuno', 'kana', 'system'
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Specifications (仕様書管理)
CREATE TABLE specifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    version INTEGER DEFAULT 1,
    status VARCHAR(50) DEFAULT 'draft', -- 'draft', 'review', 'approved'
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. Intents (Intent管理)
CREATE TABLE intents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    description TEXT NOT NULL,
    intent_type VARCHAR(100),
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    priority INTEGER DEFAULT 0,
    result JSONB,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed_at TIMESTAMP WITH TIME ZONE
);

-- 4. Notifications (通知システム)
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(100) NOT NULL,
    title VARCHAR(500) NOT NULL,
    message TEXT,
    notification_type VARCHAR(50) DEFAULT 'info', -- 'info', 'success', 'warning', 'error'
    is_read BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_messages_user_id ON messages(user_id);
CREATE INDEX idx_messages_created_at ON messages(created_at DESC);
CREATE INDEX idx_specifications_status ON specifications(status);
CREATE INDEX idx_specifications_tags ON specifications USING GIN(tags);
CREATE INDEX idx_intents_status ON intents(status);
CREATE INDEX idx_intents_created_at ON intents(created_at DESC);
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_is_read ON notifications(is_read);
```

---

## 3. ファイル構成

```
resonant-engine/
├── docker/
│   ├── docker-compose.yml          # メイン設定
│   ├── docker-compose.dev.yml      # 開発用オーバーライド
│   ├── .env.example                # 環境変数テンプレート
│   ├── .env                        # ローカル環境変数 (gitignore)
│   ├── postgres/
│   │   ├── init.sql               # 初期化SQL
│   │   └── Dockerfile             # カスタムPostgreSQLイメージ（必要に応じて）
│   └── scripts/
│       ├── start.sh               # 起動スクリプト
│       ├── stop.sh                # 停止スクリプト
│       ├── reset-db.sh            # DB初期化スクリプト
│       └── check-health.sh        # ヘルスチェック
├── .gitignore                     # .env等を除外
└── README.md                      # セットアップガイド
```

---

## 4. Docker Compose設定

### 4.1 docker-compose.yml

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

### 4.2 環境変数 (.env.example)

```bash
# PostgreSQL Configuration
POSTGRES_USER=resonant
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=resonant_dashboard
POSTGRES_PORT=5432

# Development Settings
DEBUG=true
LOG_LEVEL=DEBUG

# Application Settings (Future Sprints)
# API_HOST=0.0.0.0
# API_PORT=8000
# FRONTEND_PORT=3000
```

---

## 5. ヘルパースクリプト

### 5.1 start.sh

```bash
#!/bin/bash
set -e

echo "🚀 Starting Resonant Dashboard Environment..."

# Check .env file
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env file with your configuration"
    exit 1
fi

# Start containers
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
    sleep 1
done

echo "✅ PostgreSQL is ready!"
echo "📊 Database: resonant_dashboard"
echo "🔗 Connection: postgresql://resonant@localhost:5432/resonant_dashboard"
echo ""
echo "💡 Useful commands:"
echo "   docker-compose logs -f postgres    # View logs"
echo "   docker-compose exec postgres psql  # Connect to psql"
echo "   ./stop.sh                          # Stop environment"
```

### 5.2 check-health.sh

```bash
#!/bin/bash

echo "🔍 Checking Resonant Dashboard Environment Health..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    exit 1
fi

# Check containers
if docker-compose ps | grep -q "resonant_postgres"; then
    STATUS=$(docker inspect --format='{{.State.Health.Status}}' resonant_postgres 2>/dev/null)
    if [ "$STATUS" = "healthy" ]; then
        echo "✅ PostgreSQL: HEALTHY"
    else
        echo "⚠️  PostgreSQL: $STATUS"
    fi
else
    echo "❌ PostgreSQL container not running"
    exit 1
fi

# Test database connection
if docker-compose exec -T postgres psql -U resonant -d resonant_dashboard -c "SELECT 1;" > /dev/null 2>&1; then
    echo "✅ Database Connection: OK"
else
    echo "❌ Database Connection: FAILED"
    exit 1
fi

# Check tables
TABLES=$(docker-compose exec -T postgres psql -U resonant -d resonant_dashboard -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
echo "📊 Tables Created: $TABLES"

echo ""
echo "🎉 All health checks passed!"
```

---

## 6. 成果物

### 6.1 必須成果物
1. `docker-compose.yml` - メイン設定ファイル
2. `postgres/init.sql` - データベース初期化スクリプト
3. `.env.example` - 環境変数テンプレート
4. `scripts/start.sh` - 起動スクリプト
5. `scripts/stop.sh` - 停止スクリプト
6. `scripts/check-health.sh` - ヘルスチェック
7. `README.md` - セットアップガイド

### 6.2 期待される動作

```bash
# 1. 環境変数設定
cp .env.example .env
vim .env  # パスワード設定

# 2. 起動
./scripts/start.sh

# 3. ヘルスチェック
./scripts/check-health.sh
# Output:
# ✅ PostgreSQL: HEALTHY
# ✅ Database Connection: OK
# 📊 Tables Created: 4

# 4. 接続テスト
docker-compose exec postgres psql -U resonant -d resonant_dashboard
resonant_dashboard=# \dt
#              List of relations
#  Schema |      Name      | Type  |  Owner
# --------+----------------+-------+----------
#  public | intents        | table | resonant
#  public | messages       | table | resonant
#  public | notifications  | table | resonant
#  public | specifications | table | resonant

# 5. 停止
./scripts/stop.sh
```

---

## 7. セキュリティ考慮事項

### 7.1 開発環境
- `.env`ファイルは`.gitignore`に必ず登録
- パスワードは強力なものを使用（12文字以上、英数記号混在）
- ローカルホストのみバインド（0.0.0.0ではなく127.0.0.1）

### 7.2 本番環境準備（Sprint 5で実装）
- SSL/TLS接続の有効化
- データベースユーザー権限の最小化
- バックアップ戦略の策定
- 接続プーリングの設定

---

## 8. トラブルシューティング

### 8.1 よくある問題

| 問題 | 原因 | 解決策 |
|------|------|--------|
| コンテナが起動しない | ポート競合 | `POSTGRES_PORT`を変更 |
| パスワードエラー | .env未設定 | .envファイルを確認 |
| データが消える | ボリューム未設定 | docker-compose.ymlを確認 |
| 接続タイムアウト | ヘルスチェック未完了 | 起動完了まで待機 |

### 8.2 デバッグコマンド

```bash
# ログ確認
docker-compose logs -f postgres

# コンテナ状態確認
docker-compose ps

# 直接接続テスト
docker-compose exec postgres psql -U resonant -d resonant_dashboard

# ボリューム確認
docker volume ls | grep resonant
```

---

## 9. 次のスプリントへの準備

Sprint 2（FastAPI実装）へ進む前に以下を確認：
- [ ] PostgreSQLが安定稼働中
- [ ] 全テーブルが作成済み
- [ ] データ永続化が機能している
- [ ] ヘルスチェックが全てPASS
- [ ] README.mdが最新

---

**作成日**: 2025-11-17
**作成者**: Kana（外界翻訳層 / Claude Sonnet 4.5）
**対象**: Sprint 1実装
**前提条件**: Docker, Docker Compose インストール済み
