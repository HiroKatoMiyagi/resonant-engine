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
