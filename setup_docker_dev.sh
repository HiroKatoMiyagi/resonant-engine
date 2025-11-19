#!/bin/bash
# Resonant Engine - Docker Development Environment Setup
# Date: 2025-11-19
# Description: Unified setup script for Docker-based development environment

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="$PROJECT_ROOT/docker"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Resonant Engine - Docker環境セットアップ${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# ========================================
# 1. Pre-flight checks
# ========================================
echo -e "${YELLOW}[1/7] 事前チェック...${NC}"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Dockerがインストールされていません${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker: $(docker --version)${NC}"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Composeがインストールされていません${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker Compose: インストール済み${NC}"

echo ""

# ========================================
# 2. Environment file setup
# ========================================
echo -e "${YELLOW}[2/7] 環境変数ファイルの確認...${NC}"

if [ ! -f "$DOCKER_DIR/.env" ]; then
    echo -e "${YELLOW}⚠️  .envファイルが見つかりません${NC}"
    echo -e "${YELLOW}📝 .env.exampleから.envを作成します${NC}"
    cp "$DOCKER_DIR/.env.example" "$DOCKER_DIR/.env"

    echo -e "${RED}⚠️  IMPORTANT: .envファイルを編集してください${NC}"
    echo -e "  - POSTGRES_PASSWORD: 安全なパスワードを設定"
    echo -e "  - ANTHROPIC_API_KEY: Claude APIキーを設定"
    echo -e ""
    echo -e "  編集: ${GREEN}vi $DOCKER_DIR/.env${NC}"
    echo -e ""
    read -p "設定しましたか？ (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}❌ セットアップを中止しました${NC}"
        exit 1
    fi
fi

# Check if password is set
source "$DOCKER_DIR/.env"
if [ -z "$POSTGRES_PASSWORD" ] || [ "$POSTGRES_PASSWORD" = "your_secure_password_here" ]; then
    echo -e "${RED}❌ POSTGRES_PASSWORDが設定されていません${NC}"
    echo -e "  編集: ${GREEN}vi $DOCKER_DIR/.env${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 環境変数ファイル: 設定済み${NC}"
echo ""

# ========================================
# 3. Cleanup option
# ========================================
echo -e "${YELLOW}[3/7] クリーンアップオプション...${NC}"
echo -e "既存のDocker環境をクリーンアップしますか？"
echo -e "  ${YELLOW}警告: データベースの全データが削除されます${NC}"
echo -e ""
read -p "クリーンアップする？ (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}🧹 クリーンアップ中...${NC}"
    cd "$DOCKER_DIR"
    docker-compose down -v 2>/dev/null || true
    echo -e "${GREEN}✅ クリーンアップ完了${NC}"
else
    echo -e "${BLUE}ℹ️  既存環境を保持します${NC}"
fi
echo ""

# ========================================
# 4. Start Docker services
# ========================================
echo -e "${YELLOW}[4/7] Docker環境を起動中...${NC}"
cd "$DOCKER_DIR"

# Pull latest images
echo -e "${BLUE}📦 イメージをプル中...${NC}"
docker-compose pull

# Start services
echo -e "${BLUE}🚀 サービスを起動中...${NC}"
docker-compose up -d postgres

# Wait for PostgreSQL to be healthy
echo -e "${BLUE}⏳ PostgreSQLの起動を待機中...${NC}"
timeout=120
counter=0
until docker-compose exec -T postgres pg_isready -U resonant -d resonant_dashboard > /dev/null 2>&1; do
    counter=$((counter + 1))
    if [ $counter -ge $timeout ]; then
        echo -e "${RED}❌ タイムアウト: PostgreSQLが起動しません${NC}"
        docker-compose logs postgres
        exit 1
    fi
    printf "."
    sleep 1
done
echo ""
echo -e "${GREEN}✅ PostgreSQL起動完了${NC}"
echo ""

# ========================================
# 5. Database schema verification
# ========================================
echo -e "${YELLOW}[5/7] データベーススキーマを確認中...${NC}"

# Check pgvector extension
PGVECTOR_ENABLED=$(docker-compose exec -T postgres psql -U resonant -d resonant_dashboard -t -c "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector');" | tr -d ' ')
if [ "$PGVECTOR_ENABLED" = "t" ]; then
    echo -e "${GREEN}✅ pgvector拡張: 有効${NC}"
else
    echo -e "${RED}❌ pgvector拡張: 無効${NC}"
    exit 1
fi

# Count tables
TABLE_COUNT=$(docker-compose exec -T postgres psql -U resonant -d resonant_dashboard -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';" | tr -d ' ')
echo -e "${GREEN}✅ テーブル数: $TABLE_COUNT${NC}"

# Check critical tables
echo -e "${BLUE}📋 重要テーブルの確認:${NC}"
for table in messages intents notifications specifications claude_code_sessions memories sessions; do
    EXISTS=$(docker-compose exec -T postgres psql -U resonant -d resonant_dashboard -t -c "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = '$table');" | tr -d ' ')
    if [ "$EXISTS" = "t" ]; then
        echo -e "  ${GREEN}✅ $table${NC}"
    else
        echo -e "  ${RED}❌ $table (見つかりません)${NC}"
    fi
done
echo ""

# ========================================
# 6. Environment variables for development
# ========================================
echo -e "${YELLOW}[6/7] 開発用環境変数を設定...${NC}"

cat > "$PROJECT_ROOT/.env.docker" << EOF
# Docker Development Environment Variables
# Auto-generated by setup_docker_dev.sh
# Date: $(date)

# PostgreSQL (Docker)
DATABASE_URL=postgresql://resonant:${POSTGRES_PASSWORD}@localhost:5432/resonant_dashboard
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=resonant
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
POSTGRES_DB=resonant_dashboard

# Anthropic API
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-}

# Development
DEBUG=true
LOG_LEVEL=DEBUG
EOF

echo -e "${GREEN}✅ 環境変数ファイル: .env.docker${NC}"
echo -e "${BLUE}ℹ️  使用方法: source .env.docker${NC}"
echo ""

# ========================================
# 7. Summary and next steps
# ========================================
echo -e "${YELLOW}[7/7] セットアップ完了！${NC}"
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Docker開発環境セットアップ完了${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}📊 環境情報:${NC}"
echo -e "  データベース: ${GREEN}resonant_dashboard${NC}"
echo -e "  接続先: ${GREEN}localhost:5432${NC}"
echo -e "  ユーザー: ${GREEN}resonant${NC}"
echo -e "  テーブル数: ${GREEN}$TABLE_COUNT${NC}"
echo ""
echo -e "${BLUE}💡 次のステップ:${NC}"
echo ""
echo -e "1. 環境変数を読み込む:"
echo -e "   ${GREEN}source .env.docker${NC}"
echo ""
echo -e "2. Python仮想環境を有効化:"
echo -e "   ${GREEN}source venv/bin/activate${NC}"
echo ""
echo -e "3. テストを実行:"
echo -e "   ${GREEN}pytest tests/ -v${NC}"
echo ""
echo -e "4. データベースに接続:"
echo -e "   ${GREEN}docker-compose -f docker/docker-compose.yml exec postgres psql -U resonant -d resonant_dashboard${NC}"
echo ""
echo -e "${BLUE}🛠️  よく使うコマンド:${NC}"
echo -e "  ログ確認: ${GREEN}docker-compose -f docker/docker-compose.yml logs -f postgres${NC}"
echo -e "  停止: ${GREEN}docker-compose -f docker/docker-compose.yml down${NC}"
echo -e "  再起動: ${GREEN}docker-compose -f docker/docker-compose.yml restart postgres${NC}"
echo -e "  完全削除: ${GREEN}docker-compose -f docker/docker-compose.yml down -v${NC}"
echo ""
echo -e "${BLUE}📚 ドキュメント:${NC}"
echo -e "  README: ${GREEN}docker/README.md${NC}"
echo ""
