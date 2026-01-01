# EchoGarden 🌿

![EchoGarden Logo](https://img.shields.io/badge/EchoGarden-Growing%20Memories-4CAF50?style=for-the-badge)
[![Version](https://img.shields.io/badge/version-1.0.0-blue?style=for-the-badge)](CHANGELOG.md)
[![CI](https://github.com/meistro57/EchoGarden/actions/workflows/ci.yml/badge.svg?style=for-the-badge)](https://github.com/meistro57/EchoGarden/actions/workflows/ci.yml)
[![Tests](https://img.shields.io/badge/tests-passing-4CAF50?style=for-the-badge&logo=pytest)](tests/)
[![Python](https://img.shields.io/badge/python-3.11%2B-3776AB?style=for-the-badge&logo=python)](requirements-dev.txt)
[![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)](LICENSE)

## Transform Your ChatGPT History Into A Living Memory Garden

**EchoGarden** is your personal conversation archaeologist, semantic librarian, and AI memory bank all rolled into one. It takes your massive ChatGPT exports and transforms them into a searchable, queryable, deeply intelligent knowledge base that *remembers* everything you've ever discussed.

Built for researchers, knowledge workers, and anyone drowning in AI conversations, EchoGarden combines cutting-edge semantic search with temporal intelligence to help you rediscover insights buried in thousands of messages.

> **"Cultivate conversations, prune the noise, and harvest insights."** — The EchoGarden way.

---

## ⚡ What Makes EchoGarden Special

### 🧠 Memory That Actually Works
- **Semantic Search**: Ask in natural language, get contextually relevant answers
- **Temporal Intelligence**: Search by date, topic, or conversation thread
- **Smart Summaries**: Auto-generated context for every conversation
- **Topic Clustering**: Discover patterns across your entire conversation history

### 🤖 AI Integration That Makes Sense
- **Model Context Protocol (MCP)**: Native Claude Desktop integration
- **Multi-Provider Support**: OpenRouter, OpenAI, Anthropic, DeepSeek
- **Memory-Augmented Chat**: Your AI assistant remembers your past discussions
- **CLI Chatbot**: Talk to your conversation history in real-time

### 🏗️ Architecture You Can Trust
- **Production-Ready**: FastAPI backend, Celery workers, PostgreSQL + pgvector
- **Scalable Design**: Process thousands of conversations with ease
- **Docker-ized**: One command to rule them all
- **Modern Stack**: Next.js UI, embeddings-powered search, MinIO storage

### 🔐 Privacy First
- **Local-First**: Your data stays on your machine
- **PII Redaction**: Built-in support for scrubbing sensitive information
- **No Cloud Required**: Run everything locally, forever

---

## 🚀 Quick Start

**Choose your installation path:**
- **🐳 Path A: Docker-Only (Recommended)** - Everything runs in containers, minimal setup
- **💻 Path B: Local Development** - Run services directly on your machine, full control

---

### Path A: Docker-Only Installation (Recommended)

**Prerequisites:**
- Docker & Docker Compose
- Make (usually pre-installed on Linux/macOS)
- Python 3.11+ (only for data import and optional features)

#### Step 1: Launch All Services

```bash
git clone https://github.com/meistro57/EchoGarden.git
cd EchoGarden
make dev-up
```

This single command:
- Copies `infra/.env.example` to `infra/.env`
- Starts PostgreSQL, Redis, MinIO, API, Worker, and UI in Docker containers
- Initializes the database schema with pgvector extension

#### Step 2: Verify Installation

```bash
# Check all services are running
docker compose -f infra/docker-compose.yml ps

# Test the API
curl http://localhost:8000/health    # Should return {"status":"healthy"}
```

Now visit:
- 🌐 **Web UI**: http://localhost:3000
- 🔧 **API Docs**: http://localhost:8000/docs
- 📊 **MinIO Console**: http://localhost:9001 (credentials: `minio` / `minio123`)

#### Step 3: Set Up Python Environment for Data Import

```bash
# Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies for the import script
pip install -r ingest/requirements.txt
```

#### Step 4: Import Your ChatGPT Export

```bash
# 1. Download your data from https://chat.openai.com
#    Settings > Data Controls > Export Data
#
# 2. Wait for email with download link (can take up to 24 hours)
#
# 3. Import the zip file:
python ingest/import_chatgpt_export.py \
  --owner-id your_name \
  --db-url "postgresql://postgres:postgres@localhost:5432/postgres" \
  /path/to/conversations.zip
```

**Note:** The database URL uses `localhost:5432` because the import script runs on your host machine and connects to the containerized PostgreSQL which exposes port 5432.

#### Step 5 (Optional): Set Up Chatbot CLI

The chatbot CLI lets you chat with an AI that has access to your conversation history.

```bash
# Install additional dependencies
pip install -r mcp-requirements.txt
pip install -r api/requirements.txt

# Configure your API key in infra/.env
# Add one of these lines:
#   OPENROUTER_API_KEY=sk-or-v1-...
#   OPENAI_API_KEY=sk-...
#   ANTHROPIC_API_KEY=sk-ant-...
#   DEEPSEEK_API_KEY=sk-...

# Run the chatbot
python scripts/chatbot_cli.py --provider openrouter
```

See [docs/CHATBOT_CLI.md](docs/CHATBOT_CLI.md) for full configuration options.

#### Step 6 (Optional): Connect Claude Desktop via MCP

```bash
# Install MCP dependencies (if not already done in Step 5)
pip install -r mcp-requirements.txt

# Edit Claude Desktop config:
# macOS: ~/Library/Application Support/Claude/claude_desktop_config.json
# Linux: ~/.config/Claude/claude_desktop_config.json
# Windows: %APPDATA%\Claude\claude_desktop_config.json

# Add this configuration (replace /full/path/to with your actual path):
{
  "mcpServers": {
    "echogarden-memory": {
      "command": "python3",
      "args": ["/full/path/to/EchoGarden/mcp_server_fastmcp.py"],
      "env": {
        "API_BASE_URL": "http://localhost:8000"
      }
    }
  }
}

# Restart Claude Desktop and ask: "Search my chat history for conversations about AI"
```

See [docs/CONNECTING_AI.md](docs/CONNECTING_AI.md) for detailed MCP setup and troubleshooting.

---

### Path B: Local Development (Advanced)

**Prerequisites:**
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (for infrastructure only: PostgreSQL, Redis, MinIO)
- 4GB+ RAM

This approach runs infrastructure in Docker but runs API, Worker, and UI directly on your machine for faster iteration and debugging.

#### Step 1: Clone and Configure

```bash
git clone https://github.com/meistro57/EchoGarden.git
cd EchoGarden

# Copy environment configuration
cp infra/.env.example infra/.env

# Edit infra/.env and configure:
# - API keys (OPENAI_API_KEY, etc.)
# - Database settings (keep DATABASE_URL as is for Docker)
```

#### Step 2: Start Infrastructure Services

```bash
# Start only PostgreSQL, Redis, and MinIO in Docker
docker compose -f infra/docker-compose.yml up -d db redis minio

# Wait for services to be ready (about 10 seconds)
sleep 10

# Initialize database schema
docker compose -f infra/docker-compose.yml exec db psql -U postgres < infra/init_db.sql
```

#### Step 3: Set Up Python Environment

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install all Python dependencies
pip install -r requirements-dev.txt    # API dependencies + testing tools
pip install -r mcp-requirements.txt    # MCP server dependencies
pip install -r ingest/requirements.txt # Import script dependencies
pip install -r worker/requirements.txt # Worker dependencies
```

#### Step 4: Set Up UI

```bash
cd ui
npm install
cd ..
```

#### Step 5: Run Services in Separate Terminals

**Terminal 1 - API Server:**
```bash
source .venv/bin/activate
cd api
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Celery Worker:**
```bash
source .venv/bin/activate
cd worker
celery -A tasks worker --loglevel=info
```

**Terminal 3 - UI Development Server:**
```bash
cd ui
npm run dev
```

#### Step 6: Verify Installation

```bash
# Test endpoints
curl http://localhost:8000/health  # API
curl http://localhost:3000         # UI
```

#### Step 7: Import Data and Use Features

Now follow Steps 4-6 from Path A above to:
- Import your ChatGPT export
- Set up the chatbot CLI
- Connect Claude Desktop via MCP

---

## 🎯 Core Features

### 1. Intelligent Ingestion Pipeline
Transform raw ChatGPT exports into structured, searchable knowledge:
- ✅ Automatic normalization and validation
- ✅ Semantic embedding generation (pgvector)
- ✅ PII redaction and data sanitization
- ✅ Conversation threading and timeline reconstruction
- ✅ Metadata enrichment and tagging

### 2. High-Fidelity Search Engine
Find anything, instantly:
- 🔍 **Semantic Search**: "Show me conversations about ADHD coping strategies"
- 📅 **Temporal Filters**: "What did I learn about Docker in January 2025?"
- 🎯 **Context Retrieval**: Get full conversation threads, not just snippets
- 📊 **Topic Maps**: Visualize your conversation themes over time

### 3. Model Context Protocol (MCP) Server
Connect any MCP-compatible AI:
- 🔌 Claude Desktop integration (works today!)
- 🔮 Future ChatGPT integration (when they add MCP support)
- 🛠️ Four powerful tools:
  - `search_messages` - Semantic search across all conversations
  - `get_timeline` - Retrieve full conversation threads
  - `build_context_pack` - Create prompt-ready context bundles
  - `topic_map` - Discover discussion themes

### 4. CLI Chatbot with Memory
Talk to an AI that *remembers* your past:
```bash
python scripts/chatbot_cli.py --provider openrouter

You: What have I learned about machine learning?
[Searches your 10,000 messages, finds relevant context]
Assistant: Based on your previous conversations...
```

Supports **4 AI providers** out of the box:
- OpenRouter (100+ models, one API key)
- OpenAI (GPT-4o, GPT-4o-mini, GPT-4-turbo)
- Anthropic (Claude Opus 4, Sonnet 3.5, Haiku 3.5)
- DeepSeek (cost-effective powerhouse)

See [docs/CHATBOT_CLI.md](docs/CHATBOT_CLI.md) for the complete guide.

### 5. Modern Web Interface
Beautiful, responsive UI for browsing your memory garden:
- 📱 Mobile-friendly design
- 🎨 Clean, minimalist aesthetic
- ⚡ Real-time search results
- 📈 Conversation analytics and visualizations

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [CHANGELOG.md](CHANGELOG.md) | Version history and release notes |
| [docs/CONNECTING_AI.md](docs/CONNECTING_AI.md) | Connect Claude Desktop and other AI assistants |
| [docs/CHATBOT_CLI.md](docs/CHATBOT_CLI.md) | CLI chatbot with multi-provider support |
| [QUICKSTART_MEMORY.md](QUICKSTART_MEMORY.md) | Memory integration quick start |
| [FASTMCP_SERVER.md](FASTMCP_SERVER.md) | MCP server implementation details |

---

## 🏗️ Project Structure

```
EchoGarden/
├── api/              # FastAPI service layer + utilities
├── worker/           # Celery background workers
├── ui/               # Next.js web interface
├── infra/            # Docker Compose, PostgreSQL setup, env configs
├── ingest/           # ChatGPT export ingestion scripts
├── schemas/          # SQL schemas and migrations
├── tests/            # Pytest unit and integration tests
├── scripts/          # Dev scripts, chatbot CLI, system tests
└── docs/             # Additional documentation
```

---

## 🔧 Handy Commands

### Managing Services

```bash
# Start all services (Docker mode)
make dev-up

# Stop services (keeps data)
make dev-stop
# OR: docker compose -f infra/docker-compose.yml stop

# Stop and remove all data
make dev-down
# OR: docker compose -f infra/docker-compose.yml down --volumes

# Restart a specific service
docker compose -f infra/docker-compose.yml restart api
docker compose -f infra/docker-compose.yml restart worker
docker compose -f infra/docker-compose.yml restart ui

# View logs
docker compose -f infra/docker-compose.yml logs -f api
docker compose -f infra/docker-compose.yml logs -f worker
```

### Utility Scripts

| Script | Purpose |
|--------|---------|
| `make dev-up` | Start all services in Docker |
| `make dev-stop` | Stop all services |
| `make dev-down` | Stop and remove all containers and volumes |
| `make test` | Run end-to-end system tests |
| `./scripts/dev_seed.sh` | Populate PostgreSQL with sample data (placeholder) |
| `./scripts/test_system.py` | End-to-end smoke test for ingestion pipeline |
| `./scripts/chatbot_cli.py` | Interactive chatbot with memory integration |

---

## 🧪 Testing

### Run the Full Test Suite

```bash
source .venv/bin/activate
pytest tests -vv
```

### Run Specific Tests

```bash
pytest tests -k "pii"           # PII redaction tests only
pytest tests -k "normalization" # Input normalization tests
pytest tests/test_docker.py     # Docker build validation
```

### End-to-End Smoke Test

```bash
python scripts/test_system.py
```

### CI/CD

Every push triggers automated testing via GitHub Actions:
- Dependency installation
- Full pytest suite
- Docker build validation

Run CI locally with [act](https://github.com/nektos/act):
```bash
act -j tests
```

---

## 🎨 Use Cases

### For Researchers
- **Literature Review Memory**: Keep track of paper discussions across months
- **Hypothesis Evolution**: Trace how your thinking evolved on a topic
- **Citation Recovery**: Find that perfect quote you discussed weeks ago

### For Developers
- **Code Discussion Archive**: Remember architectural decisions and trade-offs
- **Learning Journal**: Track your progress learning new technologies
- **Debug History**: Search past troubleshooting conversations

### For Knowledge Workers
- **Meeting Notes**: Search across all AI-assisted meeting summaries
- **Project Memory**: Maintain context across long-running projects
- **Insight Mining**: Discover patterns in your thinking over time

### For Everyone
- **Personal Archive**: Your AI conversations are part of your intellectual history
- **Second Brain**: Offload memory to a system that never forgets
- **Time Machine**: Jump back to any conversation, any time

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Report Bugs**: Open an issue with detailed reproduction steps
2. **Request Features**: Describe your use case and desired functionality
3. **Submit PRs**: Fork, branch, code, test, and submit
4. **Improve Docs**: Typos, clarifications, examples are all appreciated

### Development Workflow

```bash
# 1. Fork and clone
git clone https://github.com/YOUR_USERNAME/EchoGarden.git
cd EchoGarden

# 2. Create a feature branch
git checkout -b feature/amazing-feature

# 3. Make changes and test
pytest tests

# 4. Commit with descriptive messages
git commit -m "Add amazing feature that does X"

# 5. Push and create PR
git push origin feature/amazing-feature
```

---

## 🐛 Troubleshooting

### Quick Start Issues

#### `make dev-up` fails
```bash
# Check if Docker is running
docker ps

# Check if ports are already in use
lsof -i :3000  # UI
lsof -i :8000  # API
lsof -i :5432  # PostgreSQL
lsof -i :9000  # MinIO

# Kill processes using the ports if needed
kill -9 <PID>

# Try again
make dev-down
make dev-up
```

#### Services not responding after `make dev-up`
```bash
# Check which services are running
docker compose -f infra/docker-compose.yml ps

# Check logs for errors
docker compose -f infra/docker-compose.yml logs api
docker compose -f infra/docker-compose.yml logs worker
docker compose -f infra/docker-compose.yml logs db

# Restart specific service
docker compose -f infra/docker-compose.yml restart api
```

#### API returns 500 or connection errors
```bash
# Verify database is initialized
docker compose -f infra/docker-compose.yml exec db psql -U postgres -c "\dt"

# Should show: conversations, messages, message_embeddings, etc.

# If tables missing, initialize schema:
docker compose -f infra/docker-compose.yml exec db psql -U postgres < infra/init_db.sql
```

#### Import script fails with "ModuleNotFoundError"
```bash
# Make sure you've installed the import dependencies:
pip install -r ingest/requirements.txt

# Verify installation:
pip list | grep -E "click|psycopg2|boto3|tenacity"
```

#### Database connection refused during import
```bash
# The import script runs on host, connects to Docker container
# Make sure you use localhost:5432, NOT db:5432

# Correct:
python ingest/import_chatgpt_export.py \
  --db-url "postgresql://postgres:postgres@localhost:5432/postgres" \
  /path/to/export.zip

# Wrong (this is for container-to-container communication):
# --db-url "postgresql://postgres:postgres@db:5432/postgres"
```

### Local Development Issues

#### psycopg2 build issues on macOS
- **Problem**: Missing PostgreSQL headers
- **Solution**:
```bash
brew install postgresql
# OR use binary version:
pip install psycopg2-binary
```

#### Node.js dependencies fail to install
```bash
cd ui
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps
```

#### Worker not processing tasks
```bash
# Check Redis is running
docker compose -f infra/docker-compose.yml ps redis

# Check worker logs
docker compose -f infra/docker-compose.yml logs worker

# For local development:
cd worker
celery -A tasks worker --loglevel=debug
```

### General Issues

#### Need to reset the database?
```bash
make dev-down   # Stop and remove containers + volumes
make dev-up     # Recreate with fresh volumes
```

#### Port conflicts
```bash
# Check what's using ports
lsof -i :3000  # UI (Next.js)
lsof -i :8000  # API (FastAPI)
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
lsof -i :9000  # MinIO
lsof -i :9001  # MinIO Console

# Kill conflicting processes
kill -9 <PID>
```

#### MCP Server not connecting?
See the comprehensive troubleshooting guide in [docs/CONNECTING_AI.md](docs/CONNECTING_AI.md).

#### Chatbot CLI errors?
See [docs/CHATBOT_CLI.md](docs/CHATBOT_CLI.md) for provider-specific troubleshooting.

---

## 📊 Roadmap

See [CHANGELOG.md](CHANGELOG.md) for detailed roadmap, including:

### Version 1.1.0 (Next)
- Web UI chatbot interface
- Real-time search suggestions
- Export conversation packs
- Enhanced topic clustering

### Version 1.2.0
- Multi-user support
- API authentication and rate limiting
- Usage analytics dashboard

### Version 2.0.0
- Native ChatGPT MCP integration
- Mobile applications
- Cloud deployment guides
- Enterprise features

---

## 📜 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [pgvector](https://github.com/pgvector/pgvector) - PostgreSQL vector similarity search
- [Next.js](https://nextjs.org/) - React framework for web UI
- [Celery](https://docs.celeryq.dev/) - Distributed task queue
- [Model Context Protocol](https://modelcontextprotocol.io/) - AI tool integration standard

Special thanks to the Anthropic team for creating MCP and making this kind of integration possible.

---

## ⭐ Star History

If EchoGarden helps you cultivate your conversation garden, consider giving it a star! It helps others discover the project.

---

## 🌱 Philosophy

Your conversations with AI are valuable. They represent your thinking, your questions, your growth. EchoGarden believes this knowledge shouldn't be locked away in exports or lost to time.

We're building tools that treat your AI conversations as **first-class knowledge artifacts** — searchable, queryable, and reusable. Your memory garden grows with every conversation, and EchoGarden ensures you can harvest those insights whenever you need them.

**Happy gardening!** 🌿✨

---

<div align="center">
Made with 🧠 by developers who forget things too often
</div>
