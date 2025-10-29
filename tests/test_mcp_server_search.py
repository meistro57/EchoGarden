# tests/test_mcp_server_search.py
"""Tests for the MCP server search tool behaviour."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict

import httpx

from mcp_server import EchoGardenAPI, SearchMessagesArgs


class DummySettings:
    """Minimal settings object matching the attributes used by EchoGardenAPI."""

    def __init__(self, base_url: str, timeout: float = 30.0) -> None:
        self.api_base_url = base_url
        self.request_timeout_seconds = timeout
        self.log_level = "INFO"

    @property
    def logging_level(self) -> int:
        return logging.INFO


def test_search_messages_includes_filters(monkeypatch) -> None:
    """Search tool should forward filters as JSON for the API to process."""

    captured: Dict[str, Any] = {}

    class DummyAsyncClient:
        """Minimal async HTTPX client stub capturing outgoing requests."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            captured["init_kwargs"] = kwargs
            self.base_url = str(kwargs.get("base_url", ""))

        async def __aenter__(self) -> "DummyAsyncClient":
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
            return None

        async def get(
            self, url: str, params: Dict[str, Any] | None = None
        ) -> httpx.Response:
            full_url = (
                f"{self.base_url}{url}" if self.base_url and url.startswith("/") else url
            )
            captured["request"] = {"url": full_url, "params": params or {}}
            request = httpx.Request("GET", full_url or "http://api.local/search")
            return httpx.Response(200, request=request, json={"results": []})

    monkeypatch.setattr("mcp_server.httpx.AsyncClient", DummyAsyncClient)

    settings = DummySettings(base_url="http://api.local")
    api = EchoGardenAPI(settings)

    args = SearchMessagesArgs(
        query="attention", k=5, filters={"role": "assistant", "conv_id": "abc123"}
    )
    message = asyncio.run(api.search_messages(args))

    assert message == "No results matched your search query."

    params = captured["request"]["params"]
    assert params["q"] == "attention"
    assert params["k"] == 5

    filters_payload = params["filters"]
    assert isinstance(filters_payload, str)
    assert json.loads(filters_payload) == {"role": "assistant", "conv_id": "abc123"}

    init_kwargs = captured["init_kwargs"]
    assert init_kwargs["base_url"] == "http://api.local"
    assert init_kwargs["timeout"] == settings.request_timeout_seconds
