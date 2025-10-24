# FastMCP Server for EchoGarden

## Overview

This is an alternative MCP server implementation for EchoGarden using the [fastmcp](https://github.com/jlowin/fastmcp) library. It provides the same functionality as the original `mcp_server.py` but with a simpler, more Pythonic API.

## What is FastMCP?

FastMCP is a high-level framework for building Model Context Protocol (MCP) servers. It simplifies MCP server development by:

- Using decorators (`@mcp.tool()`) instead of manual tool registration
- Automatically generating JSON schemas from function signatures and type hints
- Providing a cleaner, more intuitive API
- Reducing boilerplate code significantly

## Files

- **`mcp_server_fastmcp.py`** - The FastMCP-based server implementation
- **`mcp-requirements.txt`** - Updated with fastmcp dependency

## Installation

1. Install the dependencies:
```bash
pip install -r mcp-requirements.txt
```

Or install fastmcp directly:
```bash
pip install fastmcp>=0.2.0 httpx>=0.25.0
```

2. Make sure the EchoGarden API is running on `http://localhost:8000` (or set the `API_BASE_URL` environment variable)

## Usage

### Running the Server

```bash
# Run directly
python3 mcp_server_fastmcp.py

# Or with custom API URL
API_BASE_URL=http://your-api:8000 python3 mcp_server_fastmcp.py
```

### Configuring with Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "echogarden-memory-fastmcp": {
      "command": "python3",
      "args": ["/path/to/EchoGarden/mcp_server_fastmcp.py"],
      "env": {
        "API_BASE_URL": "http://localhost:8000"
      }
    }
  }
}
```

On Linux, the config is at: `~/.config/Claude/claude_desktop_config.json`

## Available Tools

The FastMCP server provides 5 tools:

### 1. `search_messages`
Search through your ChatGPT conversation history with semantic and full-text search.

**Parameters:**
- `query` (string, required): Search query - can be keywords or questions
- `k` (integer, optional): Number of results to return (1-200, default: 10)

**Example:**
```
Use the search_messages tool to find conversations about "machine learning"
```

### 2. `get_timeline`
Get all messages from a specific conversation in chronological order.

**Parameters:**
- `conv_id` (string, required): Conversation ID from search results

**Example:**
```
Use get_timeline with conv_id "abc123" to see the full conversation
```

### 3. `build_context_pack`
Build a context-ready text block from specific messages, respecting token limits.

**Parameters:**
- `message_ids` (array of strings, required): List of message IDs in format 'conv_id/msg_id'
- `max_tokens` (integer, optional): Maximum tokens to include (100-16384, default: 6000)
- `model` (string, optional): Model name for tokenization (e.g., 'gpt-4')

**Example:**
```
Use build_context_pack with message_ids ["conv1/msg1", "conv1/msg2"] to create a context block
```

### 4. `topic_map`
Get a topic overview of conversations over a time period.

**Parameters:**
- `from_date` (string, optional): Start date (ISO-8601 format, e.g., '2025-01-01')
- `to_date` (string, optional): End date (ISO-8601 format)
- `limit` (integer, optional): Maximum number of topics to return (default: 10)
- `min_occurrences` (integer, optional): Minimum occurrences for a topic to be included
- `sample_limit` (integer, optional): Maximum number of conversations to sample
- `max_messages` (integer, optional): Maximum number of messages to analyze

**Example:**
```
Use topic_map with from_date "2025-01-01" and to_date "2025-01-31" to see topics from January
```

### 5. `get_conversation_stats`
Get statistics for a specific conversation.

**Parameters:**
- `conv_id` (string, required): Conversation ID

**Example:**
```
Use get_conversation_stats with conv_id "abc123" to see conversation statistics
```

## Comparison: FastMCP vs Standard MCP

### Standard MCP (`mcp_server.py`)
```python
@app.list_tools()
async def list_tools() -> List[Tool]:
    return [
        Tool(
            name="search_messages",
            description="Search through your ChatGPT conversation history",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "k": {
                        "type": "integer",
                        "description": "Number of results",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    if name == "search_messages":
        # Implementation here
        ...
```

### FastMCP (`mcp_server_fastmcp.py`)
```python
@mcp.tool()
async def search_messages(query: str, k: int = 10) -> str:
    """Search through your ChatGPT conversation history.

    Args:
        query: Search query
        k: Number of results (default: 10)
    """
    # Implementation here
    ...
```

### Key Differences

| Feature | Standard MCP | FastMCP |
|---------|--------------|---------|
| **Tool Registration** | Manual via `list_tools()` | Automatic via `@mcp.tool()` decorator |
| **Schema Definition** | Manual JSON schema | Auto-generated from type hints |
| **Tool Execution** | Single `call_tool()` handler with if/else | Individual functions per tool |
| **Return Type** | `List[TextContent]` | Simple `str` |
| **Lines of Code** | ~227 lines | ~240 lines (with extra tool) |
| **Readability** | More verbose | More Pythonic |
| **Boilerplate** | High | Low |

## Advantages of FastMCP

1. **Less Boilerplate**: No need to manually write JSON schemas
2. **Type Safety**: Uses Python type hints for validation
3. **Better IDE Support**: Better autocomplete and type checking
4. **Easier to Extend**: Adding new tools is just adding a new function
5. **More Pythonic**: Follows standard Python conventions
6. **Automatic Documentation**: Docstrings become tool descriptions

## When to Use Which?

- **Use FastMCP** if you:
  - Want cleaner, more maintainable code
  - Are adding many tools
  - Prefer modern Python conventions
  - Want better IDE support

- **Use Standard MCP** if you:
  - Need maximum control over the protocol
  - Have complex tool schemas
  - Want to stay closer to the official MCP specification

## Development

### Testing the Server

To test if the server works correctly:

```bash
# Make sure the API is running
cd /path/to/EchoGarden
docker-compose up -d api

# In another terminal, run the MCP server
python3 mcp_server_fastmcp.py
```

The server will communicate via stdio, so you'll need an MCP client (like Claude Desktop) to interact with it.

### Adding New Tools

To add a new tool, simply add a new function with the `@mcp.tool()` decorator:

```python
@mcp.tool()
async def my_new_tool(param1: str, param2: int = 10) -> str:
    """Description of what this tool does.

    Args:
        param1: Description of param1
        param2: Description of param2 (default: 10)

    Returns:
        Description of return value
    """
    # Your implementation here
    return "result"
```

## Configuration

### Environment Variables

- `API_BASE_URL`: Base URL for the EchoGarden API (default: `http://localhost:8000`)

### Timeout Settings

The HTTP timeout is set to 30 seconds by default. You can modify the `HTTP_TIMEOUT` constant in the script if needed.

## Troubleshooting

### Module Not Found Error

If you get `ModuleNotFoundError: No module named 'fastmcp'`, install it:
```bash
pip install fastmcp>=0.2.0
```

### Connection Refused

If you get connection errors, make sure the EchoGarden API is running:
```bash
# Check if API is running
curl http://localhost:8000/health

# If not, start it
docker-compose up -d api
```

### Server Not Responding

The MCP server communicates via stdio. You need to use an MCP client (like Claude Desktop) to interact with it. Running it directly in the terminal won't show any output until a client connects.

## Resources

- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [EchoGarden Documentation](./README.md)
- [Connecting AI Agents Guide](./CONNECTING_AI.md)

## License

Same as EchoGarden project.
