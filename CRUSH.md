# CRUSH Configuration

## Build, Lint, and Test Commands

- **Build:**
    - `make dev-init` (Install tooling, copy env files)
    - `make dev-up` (Start API, worker, UI, and infrastructure services)
- **Lint:**
    - `ruff check .`
    - `ruff format .`
- **Test:**
    - `pytest tests` (Run all tests)
    - `pytest tests/test_specific_module.py` (Run tests for a specific module)
    - `pytest tests/test_specific_module.py::test_specific_function` (Run a single test)

## Code Style Guidelines

- **Imports:** Follow standard Python import conventions (absolute imports preferred).
- **Formatting:** Use `black` for code formatting.
- **Typing:** Utilize type hints extensively. Use `mypy` for static analysis.
- **Naming Conventions:**
    - Variables and functions: `snake_case`
    - Classes: `PascalCase`
    - Constants: `UPPER_SNAKE_CASE`
- **Error Handling:** Use custom exceptions where appropriate. Ensure exceptions are informative.
- **Directory Structure:** Organize code logically within `api/`, `worker/`, `ui/`, `ingest/` directories.
- **Configuration:** Managed via environment variables defined in `infra/.env`.
