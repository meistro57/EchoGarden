#!/bin/bash
set -e

echo "Starting dev environment..."

# Start infrastructure
cd infra
docker compose up -d

# Wait for services
echo "Waiting for services to be ready..."
sleep 15

# Check database connection
if docker compose exec db psql -U postgres -c "SELECT 1;" >/dev/null 2>&1; then
    echo "✅ Database ready"

    # Run database migrations
    docker compose exec db psql -U postgres < init_db.sql >/dev/null 2>&1
    echo "✅ Database schema initialized"
else
    echo "❌ Database not ready"
    exit 1
fi

# Load sample data if available
if [ -f "../ingest/sample_export.zip" ]; then
    echo "Loading sample data..."
    python ../ingest/import_chatgpt_export.py --db-url postgresql://postgres:postgres@localhost:5432/postgres ../ingest/sample_export.zip
else
    echo "No sample export found - place chatgpt_export.zip in ingest/ for seeding"
fi

# Make scripts executable
chmod +x ../scripts/dev_seed.sh
chmod +x ../scripts/dev_start.sh

echo "🚀 Dev environment ready!"
echo ""
echo "Services:"
echo "  API: http://localhost:8000"
echo "  UI:  http://localhost:3000"
echo "  DB:  postgres://postgres:postgres@localhost:5432/postgres"
echo ""
echo "To stop: docker compose down"