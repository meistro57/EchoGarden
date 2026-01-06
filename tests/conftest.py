# tests/conftest.py
"""Pytest configuration and compatibility shims."""

from __future__ import annotations

import sys
import types
from dataclasses import dataclass
from contextlib import asynccontextmanager
from typing import Any, Callable

from pydantic import BaseModel


try:  # pragma: no cover - exercised implicitly during imports
    import pydantic_settings  # type: ignore  # noqa: F401
except ModuleNotFoundError:  # pragma: no cover - fallback for test environment
    stub = types.ModuleType("pydantic_settings")

    class _BaseSettings(BaseModel):
        """Fallback replacement mimicking the pydantic-settings BaseSettings."""

        model_config = {}

        def model_dump(self, *args, **kwargs):  # type: ignore[override]
            return super().model_dump(*args, **kwargs)

    def _settings_config_dict(**kwargs):
        return kwargs

    stub.BaseSettings = _BaseSettings
    stub.SettingsConfigDict = _settings_config_dict
    sys.modules["pydantic_settings"] = stub


try:  # pragma: no cover - executed conditionally
    import mcp.server  # type: ignore  # noqa: F401
except ModuleNotFoundError:  # pragma: no cover - fallback stub for tests
    mcp_module = types.ModuleType("mcp")
    server_module = types.ModuleType("mcp.server")
    types_module = types.ModuleType("mcp.types")
    stdio_module = types.ModuleType("mcp.server.stdio")

    @dataclass
    class _TextContent:
        type: str
        text: str

    @dataclass
    class _InitializationOptions:
        server_name: str
        server_version: str
        capabilities: Any
        instructions: str

    @dataclass
    class _Tool:
        name: str
        description: str
        inputSchema: dict[str, Any]

    @dataclass
    class _ToolsCapability:
        pass

    @dataclass
    class _ServerCapabilities:
        tools: Any

    class _Server:
        """Minimal stub of the MCP Server used for import-time decoration."""

        def __init__(self, *_: Any, **__: Any) -> None:
            pass

        def list_tools(self) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
            def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
                return func

            return decorator

        def call_tool(self) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
            def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
                return func

            return decorator

        async def run(
            self, *_: Any, **__: Any
        ) -> None:  # pragma: no cover - unused in tests
            raise RuntimeError("Stub MCP server cannot run.")

    @asynccontextmanager
    async def _stdio_server():
        yield (None, None)

    server_module.Server = _Server
    server_module.InitializationOptions = _InitializationOptions
    stdio_module.stdio_server = _stdio_server

    types_module.Tool = _Tool
    types_module.TextContent = _TextContent
    types_module.ToolsCapability = _ToolsCapability
    types_module.ServerCapabilities = _ServerCapabilities

    mcp_module.server = server_module
    mcp_module.types = types_module
    sys.modules["mcp"] = mcp_module
    sys.modules["mcp.server"] = server_module
    sys.modules["mcp.server.stdio"] = stdio_module
    sys.modules["mcp.types"] = types_module
