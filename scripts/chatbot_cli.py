# scripts/chatbot_cli.py
"""Interactive CLI chatbot that uses EchoGarden as persistent memory."""

from __future__ import annotations

import argparse
import json
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import List, Literal, Optional, Sequence

import httpx

# Ensure local imports work when executed directly.
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from config import Settings, load_settings  # type: ignore  # noqa: E402


ChatRole = Literal["user", "assistant"]


@dataclass
class ChatTurn:
    """Single conversational turn."""

    role: ChatRole
    content: str


class MemoryClientError(RuntimeError):
    """Raised when the EchoGarden memory service cannot be reached."""


class MemoryClient:
    """Wrapper around the EchoGarden REST API for semantic memory access."""

    def __init__(self, base_url: str, timeout: float) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def search(self, query: str, limit: int) -> List[dict[str, str]]:
        if limit <= 0:
            return []
        try:
            response = httpx.get(
                f"{self._base_url}/search",
                params={"q": query, "k": limit},
                timeout=self._timeout,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise MemoryClientError(f"Unable to reach EchoGarden memory API: {exc}") from exc

        payload = response.json()
        results = payload.get("results", [])
        if not isinstance(results, list):
            return []
        formatted: List[dict[str, str]] = []
        for item in results:
            if not isinstance(item, dict):
                continue
            text = str(item.get("text", ""))
            if not text:
                continue
            formatted.append(
                {
                    "conv_id": str(item.get("conv_id", "unknown")),
                    "role": str(item.get("role", "unknown")),
                    "ts": str(item.get("ts", "")),
                    "score": f"{float(item.get('score', 0.0)):.3f}",
                    "text": text,
                }
            )
        return formatted


class LLMClientError(RuntimeError):
    """Raised when an LLM provider returns an error."""


class LLMClient:
    """Abstract base class for chat completion providers."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.timeout = settings.request_timeout

    def generate(
        self,
        history: Sequence[ChatTurn],
        user_input: str,
        *,
        system_prompt: str,
        context: Optional[str],
        temperature: float,
        max_output_tokens: int,
    ) -> str:
        raise NotImplementedError


class OpenRouterClient(LLMClient):
    """Chat completion client for the OpenRouter gateway."""

    api_url = "https://openrouter.ai/api/v1/chat/completions"

    def generate(
        self,
        history: Sequence[ChatTurn],
        user_input: str,
        *,
        system_prompt: str,
        context: Optional[str],
        temperature: float,
        max_output_tokens: int,
    ) -> str:
        api_key = self.settings.credentials.openrouter
        if not api_key:
            raise LLMClientError("OPENROUTER_API_KEY is not configured in the environment.")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        if self.settings.openrouter_site_url:
            headers["HTTP-Referer"] = self.settings.openrouter_site_url
        if self.settings.openrouter_app_name:
            headers["X-Title"] = self.settings.openrouter_app_name

        messages = _compose_openai_style_messages(history, user_input, system_prompt, context)
        payload = {
            "model": self.settings.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_output_tokens,
        }

        return _dispatch_request(self.api_url, headers, payload, self.timeout)


class OpenAIClient(LLMClient):
    """Chat completion client for the OpenAI platform."""

    api_url = "https://api.openai.com/v1/chat/completions"

    def generate(
        self,
        history: Sequence[ChatTurn],
        user_input: str,
        *,
        system_prompt: str,
        context: Optional[str],
        temperature: float,
        max_output_tokens: int,
    ) -> str:
        api_key = self.settings.credentials.openai
        if not api_key:
            raise LLMClientError("OPENAI_API_KEY is not configured in the environment.")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        messages = _compose_openai_style_messages(history, user_input, system_prompt, context)
        payload = {
            "model": self.settings.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_output_tokens,
        }

        return _dispatch_request(self.api_url, headers, payload, self.timeout)


class DeepSeekClient(LLMClient):
    """Chat completion client for DeepSeek."""

    api_url = "https://api.deepseek.com/chat/completions"

    def generate(
        self,
        history: Sequence[ChatTurn],
        user_input: str,
        *,
        system_prompt: str,
        context: Optional[str],
        temperature: float,
        max_output_tokens: int,
    ) -> str:
        api_key = self.settings.credentials.deepseek
        if not api_key:
            raise LLMClientError("DEEPSEEK_API_KEY is not configured in the environment.")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        messages = _compose_openai_style_messages(history, user_input, system_prompt, context)
        payload = {
            "model": self.settings.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_output_tokens,
        }

        return _dispatch_request(self.api_url, headers, payload, self.timeout)


class AnthropicClient(LLMClient):
    """Chat completion client for Anthropic's Messages API."""

    api_url = "https://api.anthropic.com/v1/messages"

    def generate(
        self,
        history: Sequence[ChatTurn],
        user_input: str,
        *,
        system_prompt: str,
        context: Optional[str],
        temperature: float,
        max_output_tokens: int,
    ) -> str:
        api_key = self.settings.credentials.anthropic
        if not api_key:
            raise LLMClientError("ANTHROPIC_API_KEY is not configured in the environment.")

        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        prompt = system_prompt.strip()
        if context:
            prompt = f"{prompt}\n\nRelevant EchoGarden memory:\n{context.strip()}"

        messages = [
            {"role": turn.role, "content": [{"type": "text", "text": turn.content}]}
            for turn in history
        ]
        messages.append({"role": "user", "content": [{"type": "text", "text": user_input}]})

        payload = {
            "model": self.settings.model,
            "temperature": temperature,
            "max_tokens": max_output_tokens,
            "system": prompt,
            "messages": messages,
        }

        try:
            response = httpx.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise LLMClientError(
                f"Provider returned {exc.response.status_code}: {exc.response.text}"
            ) from exc
        except httpx.HTTPError as exc:
            raise LLMClientError(f"Network error contacting provider: {exc}") from exc

        try:
            data = response.json()
        except json.JSONDecodeError as exc:
            raise LLMClientError(f"Invalid JSON from Anthropic: {exc}") from exc

        content = data.get("content", [])
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                return str(block.get("text", "")).strip()
        raise LLMClientError("Anthropic response did not contain text content.")


def _dispatch_request(url: str, headers: dict[str, str], payload: dict, timeout: float) -> str:
    """Send a POST request and return the assistant response."""

    try:
        response = httpx.post(url, headers=headers, json=payload, timeout=timeout)
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise LLMClientError(
            f"Provider returned {exc.response.status_code}: {exc.response.text}"
        ) from exc
    except httpx.HTTPError as exc:
        raise LLMClientError(f"Network error contacting provider: {exc}") from exc

    # Some providers return structured JSON and others plain text. We keep things flexible.
    content_type = response.headers.get("content-type", "")
    if "application/json" in content_type:
        data = response.json()
        return _extract_text_from_openai_style_response(data)
    return response.text


def _extract_text_from_openai_style_response(data: dict) -> str:
    """Extract assistant text from OpenAI-compatible JSON responses."""

    choices = data.get("choices", []) if isinstance(data, dict) else []
    for choice in choices:
        if not isinstance(choice, dict):
            continue
        message = choice.get("message")
        if isinstance(message, dict):
            text = message.get("content")
            if isinstance(text, str):
                return text.strip()
    raise LLMClientError("Provider response did not include assistant content.")


def _compose_openai_style_messages(
    history: Sequence[ChatTurn],
    user_input: str,
    system_prompt: str,
    context: Optional[str],
) -> List[dict[str, str]]:
    """Build OpenAI-compatible chat messages including memory context."""

    messages: List[dict[str, str]] = [{"role": "system", "content": system_prompt.strip()}]
    if context:
        messages.append(
            {
                "role": "system",
                "content": f"Relevant EchoGarden memory:\n{context.strip()}",
            }
        )
    for turn in history:
        messages.append({"role": turn.role, "content": turn.content})
    messages.append({"role": "user", "content": user_input})
    return messages


class LLMClientFactory:
    """Factory for creating provider-specific clients."""

    @staticmethod
    def create(settings: Settings) -> LLMClient:
        provider = settings.provider.lower()
        if provider == "openrouter":
            return OpenRouterClient(settings)
        if provider == "openai":
            return OpenAIClient(settings)
        if provider == "deepseek":
            return DeepSeekClient(settings)
        if provider == "anthropic":
            return AnthropicClient(settings)
        raise ValueError(f"Unsupported provider '{settings.provider}'.")


def _format_memory_snippets(results: Sequence[dict[str, str]]) -> str:
    """Render memory results as a readable context block."""

    snippets: List[str] = []
    for item in results:
        summary = textwrap.shorten(item.get("text", ""), width=220, placeholder="…")
        snippets.append(
            (
                f"- [{item.get('ts', 'unknown')} | {item.get('role', 'unknown')} | "
                f"score {item.get('score', '0.000')}] {summary}"
            )
        )
    return "\n".join(snippets)


class ChatbotCLI:
    """Interactive orchestrator that fuses LLM output with persistent memory."""

    def __init__(self, settings: Settings, *, verbose_memory: bool = False) -> None:
        self.settings = settings
        self.verbose_memory = verbose_memory
        self.memory_client = MemoryClient(settings.api_base_url, settings.request_timeout)
        self.llm_client = LLMClientFactory.create(settings)
        self.history: List[ChatTurn] = []
        self.last_memory_block: str = ""

    def handle_user_message(self, message: str) -> str:
        memory_results: List[dict[str, str]] = []
        context_block = ""
        try:
            memory_results = self.memory_client.search(message, self.settings.memory_results)
        except MemoryClientError as exc:
            context_block = ""
            if self.verbose_memory:
                print(f"[Memory warning] {exc}")
        else:
            context_block = _format_memory_snippets(memory_results)
            self.last_memory_block = context_block
            if self.verbose_memory and context_block:
                print("\n[Memory snippets]\n" + context_block + "\n")

        try:
            reply = self.llm_client.generate(
                self.history,
                message,
                system_prompt=self.settings.system_prompt,
                context=context_block or None,
                temperature=self.settings.temperature,
                max_output_tokens=self.settings.max_output_tokens,
            )
        except LLMClientError as exc:
            raise LLMClientError(f"LLM call failed: {exc}") from exc

        self.history.append(ChatTurn(role="user", content=message))
        self.history.append(ChatTurn(role="assistant", content=reply))
        return reply

    def print_history(self) -> None:
        if not self.history:
            print("Nothing to recap yet, the stage is pristine.")
            return
        print("\n=== Conversation so far ===")
        for turn in self.history:
            print(f"{turn.role.title()}: {turn.content}")
        print("===========================\n")

    def print_memory(self) -> None:
        if not self.last_memory_block:
            print("No memory snippets fetched yet, do pose another query.")
            return
        print("\n=== Last memory context ===")
        print(self.last_memory_block)
        print("===========================\n")


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Chat to your favourite model whilst raiding EchoGarden for historical context. "
            "Commands: /exit or /quit to leave, /history to review, /memory to show context."
        )
    )
    parser.add_argument(
        "--provider",
        choices=["openrouter", "openai", "deepseek", "anthropic"],
        help="Override the provider specified via CHATBOT_PROVIDER.",
    )
    parser.add_argument(
        "--model",
        help="Override the model specified via CHATBOT_MODEL.",
    )
    parser.add_argument(
        "--memory-results",
        type=int,
        help="Override CHATBOT_MEMORY_RESULTS for the current session.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        help="Override CHATBOT_TEMPERATURE for the current session.",
    )
    parser.add_argument(
        "--max-output-tokens",
        type=int,
        help="Override CHATBOT_MAX_OUTPUT_TOKENS for the current session.",
    )
    parser.add_argument(
        "--verbose-memory",
        action="store_true",
        help="Print retrieved memory snippets before each LLM call.",
    )
    return parser


def apply_overrides(settings: Settings, args: argparse.Namespace) -> Settings:
    """Return a new Settings instance with CLI overrides applied."""

    if not any(
        getattr(args, name)
        for name in ("provider", "model", "memory_results", "temperature", "max_output_tokens")
    ):
        return settings

    return Settings(
        api_base_url=settings.api_base_url,
        provider=(args.provider or settings.provider).lower(),
        model=args.model or settings.model,
        temperature=args.temperature if args.temperature is not None else settings.temperature,
        max_output_tokens=(
            args.max_output_tokens if args.max_output_tokens is not None else settings.max_output_tokens
        ),
        memory_results=args.memory_results if args.memory_results is not None else settings.memory_results,
        request_timeout=settings.request_timeout,
        system_prompt=settings.system_prompt,
        credentials=settings.credentials,
        openrouter_site_url=settings.openrouter_site_url,
        openrouter_app_name=settings.openrouter_app_name,
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    settings = load_settings()
    settings = apply_overrides(settings, args)

    chatbot = ChatbotCLI(settings, verbose_memory=args.verbose_memory)

    print(
        "\nGreetings, traveller. I'm wired into EchoGarden and ready to spin yarns with historical flair."
    )
    print("Type /exit or /quit to depart, /history for a recap, and /memory to peek at retrieved context.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nRight-o, closing the notebook. Cheerio!")
            return 0

        if not user_input:
            continue
        if user_input.lower() in {"/exit", "/quit"}:
            print("Farewell! May your next query be as riveting as this one.")
            return 0
        if user_input.lower() == "/history":
            chatbot.print_history()
            continue
        if user_input.lower() == "/memory":
            chatbot.print_memory()
            continue

        try:
            reply = chatbot.handle_user_message(user_input)
        except LLMClientError as exc:
            print(f"Oh drat, the model had a wobble: {exc}")
            continue

        print(f"Assistant: {reply}\n")


if __name__ == "__main__":
    raise SystemExit(main())

