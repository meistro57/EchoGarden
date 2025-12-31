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

## 🚀 Quick Start (< 5 minutes)

### The One-Command Wonder

```bash
git clone https://github.com/meistro57/EchoGarden.git
cd EchoGarden
make dev-init      # One-time setup: install tools, copy env files
make dev-up        # Launch the full stack (API, worker, UI, infrastructure)
```

**That's it!** Now visit:
- 🌐 **Web UI**: http://localhost:3000
- 🔧 **API Docs**: http://localhost:8000/docs
- 📊 **MinIO Console**: http://localhost:9001

### Import Your ChatGPT Export

```bash
# Download your ChatGPT data from https://chat.openai.com (Settings > Data Controls > Export)
# Then import it:
python ingest/import_chatgpt_export.py \
  --owner-id your_name \
  --db-url "postgresql://postgres:postgres@localhost:5432/postgres" \
  /path/to/conversations.zip
```

### Connect Claude Desktop for MCP Magic

See [docs/CONNECTING_AI.md](docs/CONNECTING_AI.md) for the full guide, but here's the TL;DR:

1. Edit `~/.config/Claude/claude_desktop_config.json` (or macOS/Windows equivalent)
2. Add EchoGarden MCP server config
3. Ask Claude: *"What did I say about quantum computing last month?"*
4. Watch the magic happen ✨

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

## 🛠️ Local Development

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- 4GB+ RAM (for Docker services)

### Manual Setup (if you prefer more control)

```bash
# 1. Clone and configure
git clone https://github.com/meistro57/EchoGarden.git
cd EchoGarden
cp infra/.env.example infra/.env

# 2. Start infrastructure (PostgreSQL, Redis, MinIO)
docker compose -f infra/docker-compose.yml up -d

# 3. Install Python dependencies
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
pip install -r mcp-requirements.txt

# 4. Install UI dependencies
cd ui && npm install && cd ..

# 5. Seed database (optional)
./scripts/dev_seed.sh

# 6. Run services
# Terminal 1: API
cd api && python -m uvicorn main:app --reload

# Terminal 2: Worker
cd worker && celery -A tasks worker --loglevel=info

# Terminal 3: UI
cd ui && npm run dev
```

### Handy Scripts

| Script | Purpose |
|--------|---------|
| `./scripts/dev_start.sh` | Start API, worker, and UI in orchestrated mode |
| `./scripts/dev_seed.sh` | Populate PostgreSQL with sample data |
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

### Docker won't start MinIO
- **Problem**: Port 9000 already in use
- **Solution**: `lsof -i :9000` to find the process, kill it, and restart

### psycopg2 build issues on macOS
- **Problem**: Missing PostgreSQL headers
- **Solution**: `brew install postgresql` to get the required libraries

### pytest can't import API package
- **Problem**: PYTHONPATH not set correctly
- **Solution**: Activate venv and run pytest from repo root

### Need to reset the database?
```bash
make dev-down   # Stop and remove containers
make dev-up     # Recreate with fresh volumes
```

### MCP Server not connecting?
See the comprehensive troubleshooting guide in [docs/CONNECTING_AI.md](docs/CONNECTING_AI.md).

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
