#!/usr/bin/env python3
# mcp_server.py
"""EchoGarden MCP server compatible with the OpenAI MCP specification."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, Dict, List

import httpx
from httpx import AsyncClient
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from config import Settings
from mcp.server import InitializationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    ServerCapabilities,
    TextContent,
    Tool,
    ToolsCapability,
)

LOGGER = logging.getLogger(__name__)
SETTINGS = Settings()


class SearchMessagesArgs(BaseModel):
    """Validated arguments for the search_messages tool."""

    query: str = Field(..., min_length=1, description="Search query text.")
    k: int = Field(
        default=10,
        ge=1,
        le=200,
        description="Maximum number of results to return.",
    )


class GetTimelineArgs(BaseModel):
    """Validated arguments for the get_timeline tool."""

    conv_id: str = Field(..., min_length=1, description="Conversation identifier.")


class BuildContextPackArgs(BaseModel):
    """Validated arguments for the build_context_pack tool."""

    message_ids: List[str] = Field(
        ..., min_length=1, description="Message identifiers in conv_id/msg_id format."
    )
    max_tokens: int = Field(
        default=6000,
        ge=100,
        le=16384,
        description="Maximum number of tokens to include in the context pack.",
    )


class TopicMapArgs(BaseModel):
    """Validated arguments for the topic_map tool."""

    from_: str | None = Field(
        default=None,
        alias="from",
        description="ISO-8601 start date, e.g. 2025-01-01.",
    )
    to: str | None = Field(
        default=None,
        description="ISO-8601 end date for the topic map range.",
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=200,
        description="Maximum number of topics to return.",
    )

    model_config = ConfigDict(populate_by_name=True)


class EchoGardenAPI:
    """Typed client for the EchoGarden HTTP API."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @asynccontextmanager
    async def _client(self) -> AsyncIterator[AsyncClient]:
        """Yield an AsyncClient configured for the EchoGarden API."""

        async with httpx.AsyncClient(
            base_url=str(self._settings.api_base_url),
            timeout=self._settings.request_timeout_seconds,
            follow_redirects=True,
        ) as client:
            yield client

    async def search_messages(self, args: SearchMessagesArgs) -> str:
        """Call the search endpoint and format results."""

        async with self._client() as client:
            response = await client.get("/search", params={"q": args.query, "k": args.k})
            response.raise_for_status()
            payload = response.json()

        results = payload.get("results", [])
        if not results:
            return "No results matched your search query."

        formatted: List[str] = []
        for index, hit in enumerate(results, start=1):
            snippet = (hit.get("text") or "").strip()
            if len(snippet) > 240:
                snippet = f"{snippet[:237]}..."

            formatted.append(
                "\n".join(
                    [
                        f"{index}. [{hit.get('role', 'unknown')}] {hit.get('ts', 'unknown')}",
                        f"   Conversation: {hit.get('conv_id', 'unknown')}",
                        f"   Score: {hit.get('score', 0.0):.2f}",
                        f"   {snippet}",
                    ]
                )
            )

        return f"Found {len(results)} results:\n\n" + "\n".join(formatted)

    async def get_timeline(self, args: GetTimelineArgs) -> str:
        """Fetch and format a conversation timeline."""

        async with self._client() as client:
            response = await client.get(f"/conversation/{args.conv_id}/timeline")
            response.raise_for_status()
            payload = response.json()

        messages = payload.get("messages", [])
        if not messages:
            return "No messages were returned for the requested conversation."

        formatted: List[str] = []
        for message in messages:
            formatted.append(
                "\n".join(
                    [
                        f"[{message.get('role', 'unknown')}] {message.get('ts', 'unknown')}",
                        message.get("text", ""),
                    ]
                ).strip()
            )

        return (
            f"Conversation timeline ({len(messages)} messages):\n\n"
            + "\n---\n".join(formatted)
        )

    async def build_context_pack(self, args: BuildContextPackArgs) -> str:
        """Create a context pack based on selected messages."""

        async with self._client() as client:
            response = await client.post(
                "/context/pack",
                json=args.model_dump(by_alias=True),
            )
            response.raise_for_status()
            payload = response.json()

        token_count = payload.get("token_count", 0)
        text_block = payload.get("text_block", "")
        return f"Context pack ({token_count} tokens):\n\n{text_block}"

    async def topic_map(self, args: TopicMapArgs) -> str:
        """Generate a topic overview for the requested period."""

        async with self._client() as client:
            response = await client.get("/topics", params=args.model_dump(by_alias=True))
            response.raise_for_status()
            payload = response.json()

        topics = payload.get("topics", [])
        if not topics:
            return "No topics were available for the requested period."

        formatted: List[str] = []
        for topic in topics:
            anchors = topic.get("anchors", [])
            anchor_preview = ", ".join(anchors[:3]) if anchors else "None"
            formatted.append(
                "\n".join(
                    [
                        f"• {topic.get('label', 'unknown')} (weight: {topic.get('weight', 0.0):.2f})",
                        f"  Anchors: {anchor_preview}",
                    ]
                )
            )

        return "Topic map:\n\n" + "\n\n".join(formatted)


API_CLIENT = EchoGardenAPI(SETTINGS)

app = Server("echogarden-memory")


@app.list_tools()
async def list_tools() -> List[Tool]:
    """Declare the tools exposed by this MCP server."""

    return [
        Tool(
            name="search_messages",
            description="Search conversation history with hybrid semantic and keyword retrieval.",
            inputSchema=SearchMessagesArgs.model_json_schema(),
        ),
        Tool(
            name="get_timeline",
            description="Fetch a conversation timeline in chronological order.",
            inputSchema=GetTimelineArgs.model_json_schema(),
        ),
        Tool(
            name="build_context_pack",
            description="Assemble a token-bounded context pack from selected messages.",
            inputSchema=BuildContextPackArgs.model_json_schema(),
        ),
        Tool(
            name="topic_map",
            description="Summarise topics discussed across conversations in a given period.",
            inputSchema=TopicMapArgs.model_json_schema(),
        ),
    ]


def _text_response(message: str) -> List[TextContent]:
    """Wrap a plain string response in MCP text content."""

    return [TextContent(type="text", text=message)]


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Execute a tool request against the EchoGarden API."""

    try:
        if name == "search_messages":
            params = SearchMessagesArgs.model_validate(arguments)
            return _text_response(await API_CLIENT.search_messages(params))

        if name == "get_timeline":
            params = GetTimelineArgs.model_validate(arguments)
            return _text_response(await API_CLIENT.get_timeline(params))

        if name == "build_context_pack":
            params = BuildContextPackArgs.model_validate(arguments)
            return _text_response(await API_CLIENT.build_context_pack(params))

        if name == "topic_map":
            params = TopicMapArgs.model_validate(arguments)
            return _text_response(await API_CLIENT.topic_map(params))

        LOGGER.error("Requested unknown tool: %s", name)
        return _text_response(f"Unknown tool: {name}")

    except ValidationError as exc:
        LOGGER.warning("Argument validation failed for %s: %s", name, exc)
        return _text_response(f"Invalid arguments supplied: {exc}")
    except httpx.HTTPStatusError as exc:
        LOGGER.error(
            "EchoGarden API returned %s for %s: %s", exc.response.status_code, name, exc
        )
        return _text_response(
            "The EchoGarden API returned an error while processing your request."
        )
    except httpx.HTTPError as exc:
        LOGGER.error("EchoGarden API transport error for %s: %s", name, exc)
        return _text_response(
            "The EchoGarden API could not be reached. Please confirm the server is running."
        )
    except Exception as exc:  # noqa: BLE001 - final safeguard for MCP tool execution
        LOGGER.exception("Unexpected server error handling %s", name)
        return _text_response(f"An unexpected error occurred: {exc}")


INITIALIZATION_OPTIONS = InitializationOptions(
    server_name="EchoGarden MCP Server",
    server_version="1.0.0",
    capabilities=ServerCapabilities(tools=ToolsCapability()),
    instructions=(
        "Use the available tools to search and summarise your EchoGarden chat history. "
        "Ensure the REST API is reachable at the configured base URL before invoking tools."
    ),
)


async def main() -> None:
    """Run the MCP server via stdio transport."""

    logging.basicConfig(
        level=SETTINGS.logging_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, INITIALIZATION_OPTIONS)


if __name__ == "__main__":
    asyncio.run(main())
