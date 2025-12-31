#!/usr/bin/env python3
"""FastMCP Server for EchoGarden - exposes chat memory to MCP clients like Claude Desktop.

This is an alternative implementation using the fastmcp library, which provides
a simpler, more Pythonic API compared to the standard mcp library.
"""

from typing import List, Optional
import httpx
from mcp.server.fastmcp import FastMCP
from config import Settings

# Configuration
settings = Settings()
API_BASE_URL = str(settings.api_base_url)
HTTP_TIMEOUT = settings.request_timeout_seconds

# Create FastMCP server
mcp = FastMCP("echogarden-memory")


@mcp.tool()
async def search_messages(query: str, k: int = 10) -> str:
    """Search through your ChatGPT conversation history with semantic and full-text search.

    Args:
        query: Search query - can be keywords or questions
        k: Number of results to return (1-200, default: 10)

    Returns:
        Formatted search results with conversation context
    """
    if k < 1 or k > 200:
        return "Error: k must be between 1 and 200"

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        try:
            params = {"q": query, "k": k}
            response = await client.get(f"{API_BASE_URL}/search", params=params)
            response.raise_for_status()
            data = response.json()

            results = data.get("results", [])
            if not results:
                return "No results found for your query."

            # Format each result
            formatted = []
            for i, hit in enumerate(results, 1):
                text_preview = hit['text'][:200]
                if len(hit['text']) > 200:
                    text_preview += "..."

                formatted.append(
                    f"{i}. [{hit['role']}] {hit['ts']}\n"
                    f"   Conv: {hit['conv_id']}\n"
                    f"   Message ID: {hit['msg_id']}\n"
                    f"   Score: {hit['score']:.2f}\n"
                    f"   {text_preview}\n"
                )

            return f"Found {len(results)} results:\n\n" + "\n".join(formatted)

        except httpx.HTTPError as e:
            return f"API Error: {str(e)}"
        except Exception as e:
            return f"Error: {str(e)}"


@mcp.tool()
async def get_timeline(conv_id: str) -> str:
    """Get all messages from a specific conversation in chronological order.

    Args:
        conv_id: Conversation ID from search results

    Returns:
        Complete conversation timeline with all messages
    """
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        try:
            response = await client.get(f"{API_BASE_URL}/conversation/{conv_id}/timeline")
            response.raise_for_status()
            data = response.json()

            messages = data.get("messages", [])
            if not messages:
                return f"No messages found for conversation {conv_id}"

            formatted = []
            for msg in messages:
                formatted.append(
                    f"[{msg['role']}] {msg['ts']}\n{msg['text']}\n"
                )

            return f"Conversation timeline ({len(messages)} messages):\n\n" + "\n---\n".join(formatted)

        except httpx.HTTPError as e:
            return f"API Error: {str(e)}"
        except Exception as e:
            return f"Error: {str(e)}"


@mcp.tool()
async def build_context_pack(
    message_ids: List[str],
    max_tokens: int = 6000,
    model: Optional[str] = None
) -> str:
    """Build a context-ready text block from specific messages, respecting token limits.

    This tool helps you construct a prompt-ready context from specific messages,
    ensuring you stay within token budgets for your LLM.

    Args:
        message_ids: List of message IDs in format 'conv_id/msg_id'
        max_tokens: Maximum tokens to include (100-16384, default: 6000)
        model: Optional model name for tokenization (e.g., 'gpt-4')

    Returns:
        Context pack with token count and formatted text
    """
    if max_tokens < 100 or max_tokens > 16384:
        return "Error: max_tokens must be between 100 and 16384"

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        try:
            payload = {
                "message_ids": message_ids,
                "max_tokens": max_tokens
            }
            if model:
                payload["model"] = model

            response = await client.post(
                f"{API_BASE_URL}/context/pack",
                json=payload
            )
            response.raise_for_status()
            data = response.json()

            token_count = data.get('token_count', 0)
            text_block = data.get('text_block', '')

            return f"Context Pack ({token_count} tokens):\n\n{text_block}"

        except httpx.HTTPError as e:
            return f"API Error: {str(e)}"
        except Exception as e:
            return f"Error: {str(e)}"


@mcp.tool()
async def topic_map(
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    limit: int = 10,
    min_occurrences: Optional[int] = None,
    sample_limit: Optional[int] = None,
    max_messages: Optional[int] = None
) -> str:
    """Get a topic overview of conversations over a time period.

    This tool analyzes conversations and extracts key topics with weighted importance,
    helping you understand what was discussed in a given timeframe.

    Args:
        from_date: Start date (ISO-8601 format, e.g., '2025-01-01')
        to_date: End date (ISO-8601 format)
        limit: Maximum number of topics to return (default: 10)
        min_occurrences: Minimum occurrences for a topic to be included
        sample_limit: Maximum number of conversations to sample
        max_messages: Maximum number of messages to analyze

    Returns:
        Topic map with labels, weights, and anchor terms
    """
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        try:
            params = {"limit": limit}
            if from_date:
                params["from"] = from_date
            if to_date:
                params["to"] = to_date
            if min_occurrences is not None:
                params["min_occurrences"] = min_occurrences
            if sample_limit is not None:
                params["sample_limit"] = sample_limit
            if max_messages is not None:
                params["max_messages"] = max_messages

            response = await client.get(
                f"{API_BASE_URL}/topics",
                params=params
            )
            response.raise_for_status()
            data = response.json()

            topics = data.get("topics", [])
            if not topics:
                return "No topics found for the specified time period."

            formatted = []
            for topic in topics:
                anchors = topic.get('anchors', [])[:3]
                anchor_previews = []
                for anchor in anchors:
                    if isinstance(anchor, dict):
                        text_preview = anchor.get('text', '')[:50]
                        if len(anchor.get('text', '')) > 50:
                            text_preview += "..."
                        anchor_previews.append(f"{anchor.get('conv_id', 'unknown')}: {text_preview}")
                    else:
                        anchor_previews.append(str(anchor))

                formatted.append(
                    f"• {topic['label']} (weight: {topic['weight']:.4f})\n"
                    f"  Occurrences: {topic.get('occurrences', 0)}\n"
                    f"  Sample messages: {'; '.join(anchor_previews) if anchor_previews else 'None'}"
                )

            return f"Topic Map ({len(topics)} topics):\n\n" + "\n\n".join(formatted)

        except httpx.HTTPError as e:
            return f"API Error: {str(e)}"
        except Exception as e:
            return f"Error: {str(e)}"


@mcp.tool()
async def get_conversation_stats(conv_id: str) -> str:
    """Get statistics for a specific conversation.

    Args:
        conv_id: Conversation ID

    Returns:
        Conversation statistics including message count, date range, and participants
    """
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        try:
            response = await client.get(f"{API_BASE_URL}/conversation/{conv_id}/stats")
            response.raise_for_status()
            data = response.json()

            stats = []
            stats.append(f"Conversation: {conv_id}")
            if 'message_count' in data:
                stats.append(f"Messages: {data['message_count']}")
            if 'created_at' in data:
                stats.append(f"Created: {data['created_at']}")
            if 'updated_at' in data:
                stats.append(f"Updated: {data['updated_at']}")
            if 'title' in data:
                stats.append(f"Title: {data['title']}")

            return "\n".join(stats)

        except httpx.HTTPError as e:
            return f"API Error: {str(e)}"
        except Exception as e:
            return f"Error: {str(e)}"


if __name__ == "__main__":
    # Run the FastMCP server
    mcp.run()
