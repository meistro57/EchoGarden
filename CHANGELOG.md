# Changelog

All notable changes to EchoGarden will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-12-31

### 🎉 Major Release

EchoGarden 1.0 represents a complete, production-ready memory and search platform for ChatGPT exports with AI integration.

### Added

- **Multi-Provider AI Support** 🤖
  - OpenRouter integration with 100+ models
  - OpenAI (GPT-4o, GPT-4o-mini, GPT-4-turbo)
  - Anthropic Claude (Opus 4, Sonnet 3.5, Haiku 3.5)
  - DeepSeek (chat and coder models)
  - Comprehensive provider documentation

- **Model Context Protocol (MCP) Server** 🔌
  - FastMCP-based implementation
  - OpenAI MCP specification compliance
  - Claude Desktop native integration
  - Four powerful tools: search_messages, get_timeline, build_context_pack, topic_map
  - Dual implementation (classic and FastMCP)

- **Interactive CLI Chatbot** 💬
  - Memory-augmented conversations
  - Persistent conversation history
  - Semantic memory retrieval
  - Provider-agnostic architecture
  - Verbose memory mode for debugging

- **Ingestion Pipeline** 📥
  - ChatGPT export normalization
  - PII redaction support
  - Semantic metadata enrichment
  - Timestamp handling fixes
  - Batch processing support

- **Search & Discovery** 🔍
  - High-fidelity semantic search
  - Temporal filtering
  - Contextual summaries
  - Topic mapping
  - Timeline reconstruction

- **Testing & Quality** 🧪
  - Docker build validation tests
  - Input normalization tests
  - PII redaction tests
  - End-to-end smoke tests
  - CI/CD with GitHub Actions

- **Developer Experience** 🛠️
  - Makefile automation
  - Docker Compose stack
  - Development scripts
  - Comprehensive documentation
  - Environment configuration

### Changed

- Refactored import scripts for better modularity
- Improved MCP server object naming and imports
- Enhanced search tool filter handling
- Code quality improvements across the board

### Fixed

- FastMCP import module resolution
- Server object naming in MCP implementation
- Timestamp parsing in ChatGPT exports
- Docker build context validation

### Documentation

- [CONNECTING_AI.md](docs/CONNECTING_AI.md) - Complete AI integration guide
- [CHATBOT_CLI.md](docs/CHATBOT_CLI.md) - CLI chatbot documentation
- [QUICKSTART_MEMORY.md](QUICKSTART_MEMORY.md) - Quick start guide
- [FASTMCP_SERVER.md](FASTMCP_SERVER.md) - MCP server implementation guide

## [0.3.0] - 2025-01-15

### Added
- MCP server initial implementation
- AI memory integration foundation
- FastMCP support

## [0.2.0] - 2024-12-20

### Added
- Docker validation tests
- Improved import scripts
- Enhanced error handling

## [0.1.0] - 2024-12-01

### Added
- Initial release
- Basic ingestion pipeline
- FastAPI service layer
- Celery workers
- Next.js UI
- PostgreSQL, Redis, MinIO integration

---

## Version Support

| Version | Release Date | Support Status |
|---------|-------------|----------------|
| 1.0.x   | 2025-12-31  | ✅ Active      |
| 0.3.x   | 2025-01-15  | 🔧 Maintenance |
| 0.2.x   | 2024-12-20  | ⚠️ Deprecated  |
| 0.1.x   | 2024-12-01  | ❌ Unsupported |

## Upgrade Guide

### From 0.x to 1.0

1. **Update dependencies:**
   ```bash
   pip install -r requirements-dev.txt
   pip install -r mcp-requirements.txt
   cd ui && npm install
   ```

2. **Update environment variables:**
   - Add AI provider keys (OPENROUTER_API_KEY, OPENAI_API_KEY, etc.)
   - Review `infra/.env.example` for new options

3. **Database migrations:**
   ```bash
   # No schema changes required for 1.0
   ```

4. **New features available:**
   - Try the CLI chatbot: `python scripts/chatbot_cli.py`
   - Connect Claude Desktop (see [CONNECTING_AI.md](docs/CONNECTING_AI.md))
   - Use MCP server: `python mcp_server_fastmcp.py`

## Roadmap

### 1.1.0 (Planned)
- [ ] Web UI chatbot interface
- [ ] Real-time search suggestions
- [ ] Export conversation packs
- [ ] Enhanced topic clustering

### 1.2.0 (Planned)
- [ ] Multi-user support
- [ ] API authentication
- [ ] Rate limiting
- [ ] Usage analytics

### 2.0.0 (Future)
- [ ] Native ChatGPT MCP integration
- [ ] Mobile app
- [ ] Cloud deployment guides
- [ ] Enterprise features

---

[1.0.0]: https://github.com/meistro57/EchoGarden/releases/tag/v1.0.0
[0.3.0]: https://github.com/meistro57/EchoGarden/releases/tag/v0.3.0
[0.2.0]: https://github.com/meistro57/EchoGarden/releases/tag/v0.2.0
[0.1.0]: https://github.com/meistro57/EchoGarden/releases/tag/v0.1.0
