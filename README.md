# Quick Development

## One-Command Setup
```bash
# Clone and start everything
make dev-init && make dev-up

# Or manually:
git clone <this-repo>
cp infra/.env.example infra/.env  
docker compose -f infra/docker-compose.yml up -d
./scripts/dev_start.sh
```

## Local Development Workflow
1. **Start infrastructure:** `docker compose -f infra/docker-compose.yml up -d db redis minio`
2. **Load sample data:** `./scripts/dev_seed.sh`
3. **Run API:** `cd api && python -m uvicorn main:app --reload`
4. **Run worker:** `cd worker && celery -A tasks worker --loglevel=info`  
5. **Run UI:** `cd ui && npm run dev`

## Testing
```bash
# Run system tests
python scripts/test_system.py

# Load your ChatGPT export
python ingest/import_chatgpt_export.py --owner-id your_user path/to/conversations.zip
```

## API Endpoints
- `POST /ingest/chatgpt-export` - Import conversations from ChatGPT ZIP
- `GET /search?q=...&k=50` - Hybrid search with filters
- `GET /conversation/{id}/timeline` - Get conversation messages  
- `POST /context/pack` - Build prompt-ready context blocks
- `GET /health` - Service health check

## Database Setup
```sql
psql -U postgres < infra/init_db.sql
```

## Next Steps (Milestone 2)
- Integrate vector search with embeddings
- Add MCP server mode to API  
- Topic clustering and analytics
- Improve UI with context builder workspace