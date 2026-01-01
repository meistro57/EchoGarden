#!/bin/bash
set -e

echo "Initializing EchoGarden services..."

# Change to infra directory
cd "$(dirname "$0")/../infra"

# Wait for services to be ready
echo "Waiting for database to be ready..."
sleep 15

# Check database connection
if docker compose exec db psql -U postgres -c "SELECT 1;" >/dev/null 2>&1; then
    echo "✅ Database ready"

    # Run database migrations
    docker compose exec db psql -U postgres < init_db.sql >/dev/null 2>&1 || true
    echo "✅ Database schema initialized"
else
    echo "❌ Database not ready"
    echo "Tip: Check logs with: docker compose -f infra/docker-compose.yml logs db"
    exit 1
fi

echo ""
echo "🚀 EchoGarden is ready!"
echo ""
echo "Services:"
echo "  🌐 Web UI:        http://localhost:3000"
echo "  🔧 API Docs:      http://localhost:8000/docs"
echo "  📊 MinIO Console: http://localhost:9001"
echo ""
echo "Next steps:"
echo "  1. Install Python deps: pip install -r ingest/requirements.txt"
echo "  2. Import your data:    python ingest/import_chatgpt_export.py --help"
echo ""
echo "To stop: make dev-stop"
echo "To reset: make dev-down && make dev-up"