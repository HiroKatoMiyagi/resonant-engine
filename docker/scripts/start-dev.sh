#!/bin/bash
# Start Resonant Engine Development Environment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="$(dirname "$SCRIPT_DIR")"

echo "🚀 Starting Resonant Engine Development Environment..."

cd "$DOCKER_DIR"

# Check if .env.dev exists
if [ ! -f ".env.dev" ]; then
    echo "⚠️  .env.dev not found. Creating from template..."
    cp .env.example .env.dev 2>/dev/null || cat > .env.dev << EOF
POSTGRES_USER=resonant
POSTGRES_PASSWORD=password
POSTGRES_DB=postgres
POSTGRES_PORT=5432
DEBUG=true
LOG_LEVEL=DEBUG
EOF
fi

# Stop existing containers
echo "📦 Stopping existing containers..."
docker-compose -f docker-compose.dev.yml down 2>/dev/null || true

# Start development environment
echo "🔧 Building and starting containers..."
docker-compose -f docker-compose.dev.yml --env-file .env.dev up -d --build

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 5

# Check health
echo "🔍 Checking container health..."
docker ps --format "table {{.Names}}\t{{.Status}}" | grep resonant

echo ""
echo "✅ Development environment is ready!"
echo ""
echo "📋 Quick Commands:"
echo "  - Run all tests:     docker exec resonant_dev pytest tests/ -v"
echo "  - Run Sprint 3:      docker exec resonant_dev pytest tests/memory_store/ -v"
echo "  - Run Sprint 4:      docker exec resonant_dev pytest tests/retrieval/ -v"
echo "  - Run Sprint 5:      docker exec resonant_dev pytest tests/context_assembler/ -v"
echo "  - Run Sprint 10:     docker exec resonant_dev pytest tests/acceptance/test_sprint10_acceptance.py -v"
echo "  - Run Sprint 11:     docker exec resonant_dev pytest tests/contradiction/ -v"
echo "  - Enter container:   docker exec -it resonant_dev bash"
echo "  - View logs:         docker-compose -f docker-compose.dev.yml logs -f"
echo "  - Stop environment:  docker-compose -f docker-compose.dev.yml down"
