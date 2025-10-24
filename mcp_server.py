#!/usr/bin/env python3
"""MCP Server for EchoGarden - exposes chat memory to MCP clients like Claude Desktop."""

import asyncio
import json
import sys
from typing import Any, Dict, List
import httpx
from mcp.server import Server
from mcp.types import Tool, TextContent

# Configuration
API_BASE_URL = "http://localhost:8000"

# Create MCP server
app = Server("echogarden-memory")

@app.list_tools()
async def list_tools() -> List[Tool]:
    """List all available MCP tools."""
    return [
        Tool(
            name="search_messages",
            description="Search through your ChatGPT conversation history with semantic and full-text search",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query - can be keywords or questions"
                    },
                    "k": {
                        "type": "integer",
                        "description": "Number of results to return (1-200)",
                        "minimum": 1,
                        "maximum": 200,
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_timeline",
            description="Get all messages from a specific conversation in chronological order",
            inputSchema={
                "type": "object",
                "properties": {
                    "conv_id": {
                        "type": "string",
                        "description": "Conversation ID from search results"
                    }
                },
                "required": ["conv_id"]
            }
        ),
        Tool(
            name="build_context_pack",
            description="Build a context-ready text block from specific messages, respecting token limits",
            inputSchema={
                "type": "object",
                "properties": {
                    "message_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of message IDs in format 'conv_id/msg_id'"
                    },
                    "max_tokens": {
                        "type": "integer",
                        "description": "Maximum tokens to include",
                        "default": 6000,
                        "minimum": 100,
                        "maximum": 16384
                    }
                },
                "required": ["message_ids"]
            }
        ),
        Tool(
            name="topic_map",
            description="Get a topic overview of conversations over a time period",
            inputSchema={
                "type": "object",
                "properties": {
                    "from": {
                        "type": "string",
                        "description": "Start date (ISO-8601 format, e.g., '2025-01-01')"
                    },
                    "to": {
                        "type": "string",
                        "description": "End date (ISO-8601 format)"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of topics to return",
                        "default": 10
                    }
                }
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Execute MCP tool by calling the EchoGarden API."""

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            if name == "search_messages":
                # Call search endpoint
                params = {
                    "q": arguments["query"],
                    "k": arguments.get("k", 10)
                }
                response = await client.get(f"{API_BASE_URL}/search", params=params)
                response.raise_for_status()
                data = response.json()

                # Format results
                results = data.get("results", [])
                if not results:
                    return [TextContent(
                        type="text",
                        text="No results found for your query."
                    )]

                # Format each result
                formatted = []
                for i, hit in enumerate(results, 1):
                    formatted.append(
                        f"{i}. [{hit['role']}] {hit['ts']}\n"
                        f"   Conv: {hit['conv_id']}\n"
                        f"   Score: {hit['score']:.2f}\n"
                        f"   {hit['text'][:200]}...\n"
                    )

                return [TextContent(
                    type="text",
                    text=f"Found {len(results)} results:\n\n" + "\n".join(formatted)
                )]

            elif name == "get_timeline":
                # Call timeline endpoint
                conv_id = arguments["conv_id"]
                response = await client.get(f"{API_BASE_URL}/conversation/{conv_id}/timeline")
                response.raise_for_status()
                data = response.json()

                messages = data.get("messages", [])
                formatted = []
                for msg in messages:
                    formatted.append(
                        f"[{msg['role']}] {msg['ts']}\n{msg['text']}\n"
                    )

                return [TextContent(
                    type="text",
                    text=f"Conversation timeline ({len(messages)} messages):\n\n" + "\n---\n".join(formatted)
                )]

            elif name == "build_context_pack":
                # Call context pack endpoint
                response = await client.post(
                    f"{API_BASE_URL}/context/pack",
                    json=arguments
                )
                response.raise_for_status()
                data = response.json()

                return [TextContent(
                    type="text",
                    text=f"Context Pack ({data['token_count']} tokens):\n\n{data['text_block']}"
                )]

            elif name == "topic_map":
                # Call topics endpoint
                response = await client.get(
                    f"{API_BASE_URL}/topics",
                    params=arguments
                )
                response.raise_for_status()
                data = response.json()

                topics = data.get("topics", [])
                formatted = []
                for topic in topics:
                    formatted.append(
                        f"• {topic['label']} (weight: {topic['weight']})\n"
                        f"  Anchors: {', '.join(topic.get('anchors', [])[:3])}"
                    )

                return [TextContent(
                    type="text",
                    text=f"Topic Map:\n\n" + "\n\n".join(formatted)
                )]

            else:
                return [TextContent(
                    type="text",
                    text=f"Unknown tool: {name}"
                )]

        except httpx.HTTPError as e:
            return [TextContent(
                type="text",
                text=f"API Error: {str(e)}"
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error: {str(e)}"
            )]

async def main():
    """Run the MCP server."""
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
