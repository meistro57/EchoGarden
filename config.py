# config.py
"""Configuration helpers for the EchoGarden MCP server."""

from __future__ import annotations

import logging
from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Load server configuration from environment variables and .env files."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="ECHO_GARDEN_",
    )

    api_base_url: AnyHttpUrl = Field(
        default="http://localhost:8000",
        alias="API_BASE_URL",
        description="Base URL for the EchoGarden REST API.",
    )
    request_timeout_seconds: float = Field(
        default=30.0,
        ge=1.0,
        alias="API_TIMEOUT_SECONDS",
        description="HTTP timeout for API requests in seconds.",
    )
    log_level: str = Field(
        default="INFO",
        alias="LOG_LEVEL",
        description="Python logging level for the MCP server.",
    )

    @property
    def logging_level(self) -> int:
        """Resolve the configured log level to a logging constant."""

        level = getattr(logging, self.log_level.upper(), None)
        if isinstance(level, int):
            return level
        return logging.INFO

