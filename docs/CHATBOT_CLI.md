# EchoGarden Chatbot CLI

> **Version**: 1.0.0 | [Changelog](../CHANGELOG.md)

An interactive chatbot that combines multiple AI providers with EchoGarden's semantic memory search.

## Supported AI Providers

EchoGarden chatbot supports **4 AI providers**:

| Provider | Default Model | API Endpoint |
|----------|--------------|--------------|
| **OpenRouter** | `openrouter/anthropic/claude-3.5-sonnet` | `https://openrouter.ai/api/v1/chat/completions` |
| **OpenAI** | `gpt-4o-mini` | `https://api.openai.com/v1/chat/completions` |
| **DeepSeek** | `deepseek-chat` | `https://api.deepseek.com/chat/completions` |
| **Anthropic** | `claude-3-5-sonnet-20241022` | `https://api.anthropic.com/v1/messages` |

## Quick Start

### 1. Configure API Keys

Edit your `.env` file or set environment variables:

```bash
# Choose ONE or more providers
export OPENROUTER_API_KEY="sk-or-v1-..."
export OPENAI_API_KEY="sk-..."
export DEEPSEEK_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."

# Choose your preferred provider (default: openrouter)
export CHATBOT_PROVIDER="openrouter"
```

### 2. Run the Chatbot

```bash
# With default provider (openrouter)
python scripts/chatbot_cli.py

# With a specific provider
python scripts/chatbot_cli.py --provider openai
python scripts/chatbot_cli.py --provider deepseek
python scripts/chatbot_cli.py --provider anthropic
```

## Configuration Options

### Environment Variables

All configuration can be set via environment variables:

```bash
# Provider selection
CHATBOT_PROVIDER=openrouter          # openrouter|openai|deepseek|anthropic

# Model override (optional - uses provider defaults if not set)
CHATBOT_MODEL=gpt-4o                 # Any model supported by your provider

# Generation parameters
CHATBOT_TEMPERATURE=0.3              # 0.0-1.0 (lower = more focused)
CHATBOT_MAX_OUTPUT_TOKENS=1024       # Max response length

# Memory configuration
CHATBOT_MEMORY_RESULTS=5             # Number of relevant memories to fetch
API_BASE_URL=http://localhost:8000   # EchoGarden API URL

# Request timeout
CHATBOT_REQUEST_TIMEOUT=60.0         # Seconds

# OpenRouter specific (optional)
OPENROUTER_SITE_URL=https://your-site.com
OPENROUTER_APP_NAME=EchoGarden
```

### Command Line Arguments

Override environment variables for a single session:

```bash
# Override provider
python scripts/chatbot_cli.py --provider anthropic

# Override model
python scripts/chatbot_cli.py --model gpt-4o

# Override temperature and token limit
python scripts/chatbot_cli.py --temperature 0.7 --max-output-tokens 2048

# Override memory results
python scripts/chatbot_cli.py --memory-results 10

# Show memory snippets in output
python scripts/chatbot_cli.py --verbose-memory

# Combine multiple overrides
python scripts/chatbot_cli.py --provider openai --model gpt-4o --temperature 0.8
```

## Provider-Specific Setup

### OpenRouter (Recommended)

**Why OpenRouter?**
- Access to 100+ models from multiple providers
- Single API key for OpenAI, Anthropic, Google, Meta, and more
- Pay-as-you-go pricing
- No subscription required

**Setup:**
1. Get API key from https://openrouter.ai/
2. Set environment variable:
   ```bash
   export OPENROUTER_API_KEY="sk-or-v1-..."
   ```
3. Run:
   ```bash
   python scripts/chatbot_cli.py --provider openrouter
   ```

**Available Models:**
```bash
# Claude models
CHATBOT_MODEL="openrouter/anthropic/claude-3.5-sonnet"
CHATBOT_MODEL="openrouter/anthropic/claude-opus-4"

# OpenAI models
CHATBOT_MODEL="openrouter/openai/gpt-4o"
CHATBOT_MODEL="openrouter/openai/gpt-4-turbo"

# DeepSeek via OpenRouter
CHATBOT_MODEL="openrouter/deepseek/deepseek-chat"

# And many more...
```

### OpenAI

**Setup:**
1. Get API key from https://platform.openai.com/
2. Set environment variable:
   ```bash
   export OPENAI_API_KEY="sk-..."
   ```
3. Run:
   ```bash
   python scripts/chatbot_cli.py --provider openai
   ```

**Recommended Models:**
```bash
CHATBOT_MODEL="gpt-4o"           # Latest flagship model
CHATBOT_MODEL="gpt-4o-mini"      # Fast and efficient (default)
CHATBOT_MODEL="gpt-4-turbo"      # Previous generation
```

### DeepSeek

**Why DeepSeek?**
- Cost-effective Chinese LLM
- Strong performance on coding and reasoning
- Very competitive pricing

**Setup:**
1. Get API key from https://platform.deepseek.com/
2. Set environment variable:
   ```bash
   export DEEPSEEK_API_KEY="sk-..."
   ```
3. Run:
   ```bash
   python scripts/chatbot_cli.py --provider deepseek
   ```

**Available Models:**
```bash
CHATBOT_MODEL="deepseek-chat"      # Default
CHATBOT_MODEL="deepseek-coder"     # Optimized for code
```

### Anthropic Claude

**Setup:**
1. Get API key from https://console.anthropic.com/
2. Set environment variable:
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-..."
   ```
3. Run:
   ```bash
   python scripts/chatbot_cli.py --provider anthropic
   ```

**Available Models:**
```bash
CHATBOT_MODEL="claude-3-5-sonnet-20241022"  # Default, best balance
CHATBOT_MODEL="claude-opus-4-20250514"       # Most capable
CHATBOT_MODEL="claude-3-5-haiku-20241022"    # Fastest
```

## Interactive Commands

While chatting, you can use these commands:

| Command | Description |
|---------|-------------|
| `/exit` or `/quit` | Exit the chatbot |
| `/history` | Show conversation history |
| `/memory` | Show last memory context retrieved |

## Examples

### Basic Usage

```bash
$ python scripts/chatbot_cli.py --provider openai

Greetings, traveller. I'm wired into EchoGarden and ready to spin yarns with historical flair.
Type /exit or /quit to depart, /history for a recap, and /memory to peek at retrieved context.

You: What did I say about quantum computing?
[Memory snippets retrieved from your ChatGPT history...]
Assistant: Based on your past conversations, you've discussed...
```

### Switching Providers

```bash
# Try OpenRouter with Claude
python scripts/chatbot_cli.py --provider openrouter --model "openrouter/anthropic/claude-opus-4"

# Try DeepSeek
python scripts/chatbot_cli.py --provider deepseek --verbose-memory

# Try OpenAI's latest
python scripts/chatbot_cli.py --provider openai --model gpt-4o
```

### Advanced Configuration

```bash
# High creativity mode with more memory
python scripts/chatbot_cli.py \
  --provider anthropic \
  --temperature 0.9 \
  --max-output-tokens 4096 \
  --memory-results 15 \
  --verbose-memory

# Fast and focused with minimal memory
python scripts/chatbot_cli.py \
  --provider openai \
  --model gpt-4o-mini \
  --temperature 0.1 \
  --memory-results 3
```

## How Memory Integration Works

1. **You ask a question** → Chatbot sends it to EchoGarden API
2. **Semantic search** → API finds relevant past conversations
3. **Context injection** → Chatbot includes top N results in prompt
4. **AI generates response** → Using both your question AND relevant memories
5. **Conversational continuity** → All exchanges stay in session history

### Memory Search Example

```
You: Tell me about my ADHD strategies

[Behind the scenes:]
1. Searches EchoGarden: "ADHD strategies"
2. Finds 5 relevant past conversations
3. Injects them as context: "Relevant EchoGarden memory: ..."
4. AI responds with awareness of your past discussions
```

### Verbose Memory Mode

Enable `--verbose-memory` to see what memories are retrieved:

```bash
$ python scripts/chatbot_cli.py --verbose-memory

You: What did I learn about Docker?

[Memory snippets]
- [2025-01-15 | user | score 0.892] I'm trying to understand Docker networking...
- [2025-01-16 | assistant | score 0.854] Docker uses bridge networks by default...
- [2024-12-10 | user | score 0.821] How do I persist data in Docker?
- [2024-12-10 | assistant | score 0.789] You can use volumes or bind mounts...
- [2025-01-20 | user | score 0.756] Docker Compose is confusing me with...
Assistant: Based on your Docker learning, here are the key concepts...


## Troubleshooting

### API Key Not Found

```bash
Error: OPENROUTER_API_KEY is not configured in the environment.
```

**Solution:** Set the API key for your chosen provider:
```bash
export OPENROUTER_API_KEY="your-key-here"
# Or add to .env file
```

### Memory API Connection Refused

```bash
[Memory warning] Unable to reach EchoGarden memory API: Connection refused
```

**Solution:** Ensure EchoGarden API is running:
```bash
# Check if running
curl http://localhost:8000/health

# Start if not running
cd api && python -m uvicorn main:app --reload
```

### Provider Error Responses

```bash
Provider returned 429: Rate limit exceeded
Provider returned 401: Invalid authentication credentials
Provider returned 500: Internal server error
```

**Solutions:**
- **429**: Rate limited - wait a few minutes or upgrade your plan
- **401**: Invalid API key - check your credentials
- **500**: Provider issue - wait and retry, or try a different provider

### Wrong Model for Provider

```bash
Provider returned 404: Model not found
```

**Solution:** Use the correct model for your provider. Check provider documentation or use defaults.

## Architecture

### Code Structure

```
scripts/
├── chatbot_cli.py          # Main chatbot implementation
│   ├── LLMClient           # Abstract base class
│   ├── OpenRouterClient    # OpenRouter implementation
│   ├── OpenAIClient        # OpenAI implementation
│   ├── DeepSeekClient      # DeepSeek implementation
│   ├── AnthropicClient     # Anthropic implementation
│   └── LLMClientFactory    # Provider selection
└── config.py               # Configuration loader
    ├── ProviderCredentials # API key storage
    └── Settings            # Runtime settings
```

### Request Flow

```
User Input
    ↓
Memory Search (EchoGarden API)
    ↓
Context Retrieval
    ↓
LLM Client Factory (Select Provider)
    ↓
Provider-Specific Client
    ↓
HTTP Request to AI Provider
    ↓
Response Parsing
    ↓
Display to User
```

### Adding a New Provider

Want to add a new AI provider? Follow these steps:

1. **Update `scripts/config.py`:**
   ```python
   @dataclass(frozen=True)
   class ProviderCredentials:
       # ... existing providers ...
       groq: Optional[str]  # Add new provider
   
   def load_settings() -> Settings:
       credentials = ProviderCredentials(
           # ... existing ...
           groq=_get_env("GROQ_API_KEY"),
       )
   
   def _default_model_for_provider(provider: str) -> str:
       defaults = {
           # ... existing ...
           "groq": "mixtral-8x7b-32768",
       }
   ```

2. **Create provider class in `scripts/chatbot_cli.py`:**
   ```python
   class GroqClient(LLMClient):
       api_url = "https://api.groq.com/openai/v1/chat/completions"
       
       def generate(self, history, user_input, *, system_prompt, context, temperature, max_output_tokens) -> str:
           api_key = self.settings.credentials.groq
           if not api_key:
               raise LLMClientError("GROQ_API_KEY is not configured.")
           
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
   ```

3. **Register in factory:**
   ```python
   @staticmethod
   def create(settings: Settings) -> LLMClient:
       provider = settings.provider.lower()
       # ... existing providers ...
       if provider == "groq":
           return GroqClient(settings)
       raise ValueError(f"Unsupported provider '{settings.provider}'.")
   ```

4. **Update CLI choices:**
   ```python
   parser.add_argument(
       "--provider",
       choices=["openrouter", "openai", "deepseek", "anthropic", "groq"],
       help="Override the provider specified via CHATBOT_PROVIDER.",
   )
   ```

## Cost Comparison

Approximate costs per million tokens (as of December 2025):

| Provider | Model | Input | Output |
|----------|-------|-------|--------|
| OpenRouter | Various | Varies | Varies |
| OpenAI | gpt-4o-mini | $0.15 | $0.60 |
| OpenAI | gpt-4o | $2.50 | $10.00 |
| DeepSeek | deepseek-chat | $0.14 | $0.28 |
| Anthropic | claude-3-5-sonnet | $3.00 | $15.00 |
| Anthropic | claude-opus-4 | $15.00 | $75.00 |

**Note:** Prices may vary. Check provider websites for current rates.

## Performance Tips

1. **Use faster models for iteration**: `gpt-4o-mini`, `claude-3-5-haiku`, or `deepseek-chat`
2. **Lower temperature for focused responses**: `--temperature 0.1`
3. **Limit memory results**: `--memory-results 3` for faster queries
4. **Use OpenRouter for flexibility**: Switch models without changing code
5. **Batch related questions**: Keep conversation going to maintain context

## Privacy & Security

- **API keys**: Never commit to git. Use `.env` files (already in `.gitignore`)
- **Local processing**: Chatbot runs locally, only sends prompts to AI providers
- **Memory data**: Stays in your local database, not sent to AI providers (unless retrieved as context)
- **PII redaction**: EchoGarden supports PII redaction (see `infra/.env.example`)

## Related Documentation

- [EchoGarden README](../README.md) - Project overview
- [Connecting AI](./CONNECTING_AI.md) - MCP server setup for Claude Desktop
- [Quick Start Memory](../QUICKSTART_MEMORY.md) - Getting started guide

## Support

- GitHub Issues: https://github.com/meistro57/EchoGarden/issues
- API Docs: http://localhost:8000/docs (when running)
- Provider Docs:
  - OpenRouter: https://openrouter.ai/docs
  - OpenAI: https://platform.openai.com/docs
  - DeepSeek: https://platform.deepseek.com/api-docs
  - Anthropic: https://docs.anthropic.com/

---

**Happy chatting with your memory-augmented AI!** 🌿🤖
