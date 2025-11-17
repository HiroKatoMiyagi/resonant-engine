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
