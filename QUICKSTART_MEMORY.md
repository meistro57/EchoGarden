# 🧠 Quick Start: Using Your ChatGPT Memory

> **Version**: 1.0.0 | [Changelog](CHANGELOG.md)

Your EchoGarden is now loaded with **1,859 conversations** and **56,801 messages**!

## ✅ What's Working Right Now

1. **Web UI**: http://localhost:3000 - Search and browse your history
2. **REST API**: http://localhost:8000 - Direct API access
3. **Python Script**: Query from command line
4. **MCP Server**: Ready for Claude Desktop

## 🚀 Try It Now!

### Option 1: Web UI (Easiest)
```bash
# Open in your browser
firefox http://localhost:3000  # or chrome/edge
```

### Option 2: Python Script (Quick)
```bash
# Search your memory
python3 scripts/query_memory.py search "ADHD" 5
python3 scripts/query_memory.py search "quantum physics" 10

# Get a conversation timeline
python3 scripts/query_memory.py timeline <conv-id-from-search>
```

### Option 3: Claude Desktop (Most Powerful)

1. **Install Claude Desktop** from https://claude.ai/download

2. **Configure MCP** - Create/edit config file:

   **Linux**: `~/.config/Claude/claude_desktop_config.json`
   **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

3. **Add this configuration**:
```json
{
  "mcpServers": {
    "echogarden-memory": {
      "command": "python3",
      "args": [
        "/home/mark/EchoGarden/mcp_server.py"
      ],
      "env": {
        "API_BASE_URL": "http://localhost:8000"
      }
    }
  }
}
```

4. **Restart Claude Desktop**

5. **Ask Claude things like**:
   - "Search my chat history for conversations about ADHD"
   - "What did I discuss about quantum physics?"
   - "Show me topics from January 2025"
   - "Get the conversation timeline for [conv_id from search]"

### Option 4: API Direct
```bash
# Search
curl "http://localhost:8000/search?q=ADHD&k=10" | jq

# Get topics
curl "http://localhost:8000/topics?from=2025-01-01&to=2025-12-31" | jq

# API docs
firefox http://localhost:8000/docs
```

## 📖 Full Documentation

- **Detailed Setup**: [docs/CONNECTING_AI.md](docs/CONNECTING_AI.md)
- **Main README**: [README.md](README.md)
- **API Docs**: http://localhost:8000/docs

## 🔧 Maintaining Your Memory

### Import New ChatGPT Exports
```bash
# Export from ChatGPT (Settings → Data Controls → Export)
# Then import:
python ingest/import_chatgpt_export.py \
  --db-url "postgresql://postgres:postgres@localhost:5432/postgres" \
  --owner-id mark \
  /path/to/new-export.zip
```

### Check Database Stats
```bash
docker compose -f infra/docker-compose.yml exec db psql -U postgres -c \
  "SELECT COUNT(*) as conversations FROM conversations;"

docker compose -f infra/docker-compose.yml exec db psql -U postgres -c \
  "SELECT COUNT(*) as messages FROM messages;"
```

### Restart Services
```bash
# Restart everything
docker compose -f infra/docker-compose.yml restart

# Or rebuild if you made changes
docker compose -f infra/docker-compose.yml up --build -d
```

## 🎯 What Can You Do?

With your memory connected, you can:

✅ **Search semantically** - Find conversations by meaning, not just keywords
✅ **Time travel** - See what you discussed months or years ago
✅ **Build context** - Grab relevant past conversations to inform current chats
✅ **Discover topics** - See what themes emerge over time
✅ **Never lose insights** - All your ChatGPT wisdom is searchable forever

## 🤖 For Future ChatGPT Integration

ChatGPT doesn't support MCP yet, but when it does:

1. The same `mcp_server.py` will work
2. Or use Custom GPT Actions (requires public URL)
3. Or use OpenAI Assistant API with function calling

See [docs/CONNECTING_AI.md](docs/CONNECTING_AI.md) for these options.

## 💡 Examples

### Find Old Conversations
```bash
python3 scripts/query_memory.py search "that time I asked about quantum" 5
```

### Check What You Learned
Ask Claude: "Search my history for all technical things I learned about Docker"

### Build Context for Current Chat
1. Search for relevant past conversations
2. Get their conv_ids
3. Ask Claude to build a context pack
4. Use that to inform your current chat

## 🆘 Troubleshooting

**API not responding?**
```bash
docker compose -f infra/docker-compose.yml ps
curl http://localhost:8000/health
```

**No results found?**
```bash
# Check data was imported
docker compose -f infra/docker-compose.yml exec db psql -U postgres -c \
  "SELECT COUNT(*) FROM messages;"
```

**Claude Desktop not connecting?**
- Check config file location
- Restart Claude Desktop
- Check logs: `~/Library/Logs/Claude/` (macOS)

## 🌟 Status

- ✅ Database: Running with 56,801 messages
- ✅ API: http://localhost:8000
- ✅ Worker: Processing embeddings
- ✅ UI: http://localhost:3000
- ✅ MCP Server: Ready for Claude Desktop

Your memory garden is growing! 🌱
