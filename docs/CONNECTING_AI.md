# Connecting AI Assistants to EchoGarden Memory

This guide shows you how to connect AI assistants (Claude Desktop, custom scripts, or future ChatGPT) to your EchoGarden conversation memory using the Model Context Protocol (MCP).

## Prerequisites

1. EchoGarden running: `docker compose -f infra/docker-compose.yml up -d`
2. Data imported: `python ingest/import_chatgpt_export.py --db-url "postgresql://postgres:postgres@localhost:5432/postgres" --owner-id your_name /path/to/export.zip`
3. MCP dependencies installed: `pip install -r mcp-requirements.txt`

## Option 1: Claude Desktop (Recommended)

Claude Desktop has native MCP support. Configure it to use your EchoGarden memory:

### Setup Steps

1. **Install Claude Desktop** from https://claude.ai/download

2. **Configure MCP Server** - Edit Claude Desktop's config file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
**Linux:** `~/.config/Claude/claude_desktop_config.json`

Add this configuration:

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

3. **Restart Claude Desktop**

4. **Test It** - Ask Claude:
   - "Search my chat history for conversations about AI"
   - "What did I say about ADHD last month?"
   - "Get me the conversation timeline for [conv_id]"

### Available Tools

Claude will have access to these tools:

- **search_messages** - Search your ChatGPT history semantically
- **get_timeline** - View full conversation threads
- **build_context_pack** - Build prompt-ready context from selected messages
- **topic_map** - Get topic overview for time periods

## Option 2: Custom Python Script

Create your own script to query your memory:

```python
#!/usr/bin/env python3
import subprocess
import json
import sys

def call_mcp_tool(tool_name, arguments):
    """Call an MCP tool and return the result."""
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    }

    # Run MCP server
    process = subprocess.Popen(
        ["python3", "/home/mark/EchoGarden/mcp_server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Send request
    stdout, stderr = process.communicate(input=json.dumps(request))

    try:
        result = json.loads(stdout)
        return result.get("result", {})
    except json.JSONDecodeError:
        return {"error": f"Failed to parse response: {stdout}"}

# Example: Search for ADHD conversations
if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "ADHD"

    result = call_mcp_tool("search_messages", {
        "query": query,
        "k": 5
    })

    print(json.dumps(result, indent=2))
```

Save as `query_memory.py` and run:
```bash
python3 query_memory.py "your search query"
```

## Option 3: Direct API Access

For simpler use cases, query the FastAPI directly:

```bash
# Search conversations
curl "http://localhost:8000/search?q=ADHD&k=10"

# Get conversation timeline
curl "http://localhost:8000/conversation/{conv_id}/timeline"

# Get topics
curl "http://localhost:8000/topics?from=2025-01-01&to=2025-12-31"
```

### Python Example

```python
import httpx

async def search_memory(query: str, limit: int = 10):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/search",
            params={"q": query, "k": limit}
        )
        return response.json()

# Use it
import asyncio
results = asyncio.run(search_memory("quantum physics"))
print(results)
```

## Option 4: Future ChatGPT Integration

When ChatGPT adds MCP support, configuration will be similar to Claude Desktop. For now, you can:

### A) Custom GPT with Actions (Public URL Required)

If you expose your EchoGarden API publicly (via ngrok, cloudflare tunnel, etc):

1. Create a Custom GPT in ChatGPT
2. Add this OpenAPI schema in Actions:

```yaml
openapi: 3.0.0
info:
  title: EchoGarden Memory
  version: 0.3.0
servers:
  - url: https://your-public-url.com
paths:
  /search:
    get:
      operationId: searchMessages
      summary: Search chat history
      parameters:
        - name: q
          in: query
          required: true
          schema:
            type: string
        - name: k
          in: query
          schema:
            type: integer
            default: 10
      responses:
        '200':
          description: Search results
```

### B) Via Assistant API (Code)

```python
from openai import OpenAI
import httpx

client = OpenAI()

# Define function for searching memory
def search_echogarden(query: str):
    response = httpx.get(
        "http://localhost:8000/search",
        params={"q": query, "k": 5}
    )
    return response.json()

# Use with Assistant API
assistant = client.beta.assistants.create(
    name="Memory Assistant",
    instructions="You have access to my full ChatGPT conversation history via search_memory.",
    tools=[{
        "type": "function",
        "function": {
            "name": "search_memory",
            "description": "Search through chat history",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        }
    }]
)
```

## Troubleshooting

### MCP Server Won't Start
```bash
# Test the MCP server manually
python3 /home/mark/EchoGarden/mcp_server.py

# Check API is running
curl http://localhost:8000/health
```

### Claude Desktop Not Finding MCP Server
- Check config file path is correct
- Verify Python3 is in PATH
- Check logs: `~/Library/Logs/Claude/` (macOS) or `%APPDATA%\Claude\logs\` (Windows)

### API Connection Refused
```bash
# Make sure services are running
docker compose -f infra/docker-compose.yml ps

# Restart if needed
docker compose -f infra/docker-compose.yml restart api
```

### Permission Errors
```bash
# Make MCP server executable
chmod +x /home/mark/EchoGarden/mcp_server.py
```

## Examples

### Search for Specific Topics
```
Ask Claude: "Search my chat history for conversations about quantum physics"
```

### Get Conversation Context
```
Ask Claude: "Get the timeline for conversation 67b88f7b-2100-8004-8e80-8b445d2c93bc"
```

### Build Context Pack
```
Ask Claude: "Build a context pack from these message IDs: [list of IDs] with max 4000 tokens"
```

### Topic Discovery
```
Ask Claude: "Show me the topics I discussed in January 2025"
```

## Advanced: Exposing to Internet

To use with ChatGPT Custom Actions, expose your API:

### Using Cloudflare Tunnel (Free)
```bash
# Install cloudflared
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared
chmod +x cloudflared

# Create tunnel
./cloudflared tunnel --url http://localhost:8000
```

### Using ngrok
```bash
# Install ngrok from https://ngrok.com
ngrok http 8000
```

**Security Warning:** Only expose publicly if you add authentication to your API!

## Next Steps

1. ✅ Import your ChatGPT history
2. ✅ Test search via web UI (http://localhost:3000)
3. 🎯 Connect Claude Desktop using steps above
4. 🎯 Create custom scripts for specific queries
5. 🎯 Wait for ChatGPT MCP support (or use Custom Actions)

## Need Help?

- Check the [main README](../README.md)
- View API docs: http://localhost:8000/docs
- Open an issue on GitHub
