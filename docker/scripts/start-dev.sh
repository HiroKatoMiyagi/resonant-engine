#!/bin/bash
# Start development environment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="$(dirname "$SCRIPT_DIR")"

cd "$DOCKER_DIR"

echo "🚀 Starting Resonant Development Environment..."

# Check if .env.dev exists
if [ ! -f .env.dev ]; then
    echo "⚠️  .env.dev not found, creating from example..."
    cp .env.example .env.dev
fi

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f docker-compose.dev.yml --env-file .env.dev down

# Build and start services
echo "🔨 Building development containers..."
docker-compose -f docker-compose.dev.yml --env-file .env.dev build

echo "▶️  Starting services..."
docker-compose -f docker-compose.dev.yml --env-file .env.dev up -d

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 5

# Check health
echo "🏥 Checking service health..."
docker-compose -f docker-compose.dev.yml --env-file .env.dev ps

echo ""
echo "✅ Development environment is ready!"
echo ""
echo "📝 Available commands:"
echo "  - Run tests:           docker exec resonant_dev pytest tests/"
echo "  - Run specific test:   docker exec resonant_dev pytest tests/contradiction/"
echo "  - Enter container:     docker exec -it resonant_dev bash"
echo "  - View logs:           docker-compose -f docker-compose.dev.yml logs -f"
echo "  - Stop environment:    docker-compose -f docker-compose.dev.yml down"
echo ""
echo "🔗 Services:"
echo "  - PostgreSQL:  localhost:5432"
echo "  - API:         localhost:8000"
echo ""
