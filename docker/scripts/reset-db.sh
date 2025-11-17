#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

echo "⚠️  WARNING: This will delete all data in the database!"
read -p "Are you sure? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Cancelled."
    exit 0
fi

echo "🗑️  Resetting database..."

docker-compose down -v
docker volume rm resonant_postgres_data 2>/dev/null || true

echo "✅ Database reset complete"
echo "Run ./scripts/start.sh to recreate the database"
