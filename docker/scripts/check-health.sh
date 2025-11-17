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
