# scripts/config.py
"""Configuration helpers for the EchoGarden CLI chatbot."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Optional


@dataclass(frozen=True)
class ProviderCredentials:
    """Authentication tokens for each supported provider."""

    openrouter: Optional[str]
    openai: Optional[str]
    deepseek: Optional[str]
    anthropic: Optional[str]


@dataclass(frozen=True)
class Settings:
    """Runtime configuration for the chatbot."""

    api_base_url: str
    provider: str
    model: str
    temperature: float
    max_output_tokens: int
    memory_results: int
    request_timeout: float
    system_prompt: str
    credentials: ProviderCredentials
    openrouter_site_url: Optional[str]
    openrouter_app_name: Optional[str]


def _parse_dotenv_line(line: str) -> Optional[tuple[str, str]]:
    """Parse a single .env line, returning a key/value pair when valid."""

    if not line:
        return None
    if line.startswith("#"):
        return None
    if "=" not in line:
        return None
    key, value = line.split("=", 1)
    key = key.strip()
    value = value.strip().strip("\"\'")
    if not key:
        return None
    return key, value


def load_dotenv(paths: Optional[Iterable[Path]] = None) -> Dict[str, str]:
    """Load environment variables from .env files without overriding existing values."""

    if paths is None:
        cwd = Path.cwd()
        paths = (cwd / ".env", cwd.parent / ".env")

    loaded: Dict[str, str] = {}
    for path in paths:
        if not path or not path.exists():
            continue
        try:
            for raw_line in path.read_text(encoding="utf-8").splitlines():
                parsed = _parse_dotenv_line(raw_line.strip())
                if not parsed:
                    continue
                key, value = parsed
                if key not in os.environ:
                    os.environ[key] = value
                    loaded[key] = value
        except OSError as exc:
            # Swallow filesystem errors but record the failure for debugging purposes.
            loaded[f"__error__::{path}"] = str(exc)
    return loaded


def _get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    """Fetch an environment variable, returning a default when unset."""

    value = os.environ.get(name)
    if value is not None:
        return value
    return default


def _get_float(name: str, default: float) -> float:
    try:
        value = _get_env(name)
        return float(value) if value is not None else default
    except ValueError:
        return default


def _get_int(name: str, default: int) -> int:
    try:
        value = _get_env(name)
        return int(value) if value is not None else default
    except ValueError:
        return default


def load_settings() -> Settings:
    """Load settings from environment variables, applying sensible defaults."""

    load_dotenv()

    credentials = ProviderCredentials(
        openrouter=_get_env("OPENROUTER_API_KEY"),
        openai=_get_env("OPENAI_API_KEY"),
        deepseek=_get_env("DEEPSEEK_API_KEY"),
        anthropic=_get_env("ANTHROPIC_API_KEY"),
    )

    provider = (_get_env("CHATBOT_PROVIDER", "openrouter") or "openrouter").lower()
    model = _get_env("CHATBOT_MODEL", "") or _default_model_for_provider(provider)
    temperature = _get_float("CHATBOT_TEMPERATURE", 0.3)
    max_tokens = _get_int("CHATBOT_MAX_OUTPUT_TOKENS", 1024)
    memory_results = _get_int("CHATBOT_MEMORY_RESULTS", 5)
    request_timeout = _get_float("CHATBOT_REQUEST_TIMEOUT", 60.0)

    system_prompt = _get_env(
        "CHATBOT_SYSTEM_PROMPT",
        (
            "You are an insightful research assistant helping Mark. "
            "Blend new user queries with historical context from EchoGarden memory while being concise."
        ),
    )

    return Settings(
        api_base_url=_get_env("API_BASE_URL", "http://localhost:8000"),
        provider=provider,
        model=model,
        temperature=temperature,
        max_output_tokens=max_tokens,
        memory_results=max(0, memory_results),
        request_timeout=request_timeout,
        system_prompt=system_prompt,
        credentials=credentials,
        openrouter_site_url=_get_env("OPENROUTER_SITE_URL"),
        openrouter_app_name=_get_env("OPENROUTER_APP_NAME"),
    )


def _default_model_for_provider(provider: str) -> str:
    """Return provider-specific default model identifiers."""

    defaults = {
        "openrouter": "openrouter/anthropic/claude-3.5-sonnet",
        "openai": "gpt-4o-mini",
        "deepseek": "deepseek-chat",
        "anthropic": "claude-3-5-sonnet-20241022",
    }
    return defaults.get(provider, "gpt-4o-mini")

