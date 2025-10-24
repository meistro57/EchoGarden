# CRUSH Configuration

## Build, Lint, and Test Commands

- **Build:**
    - `make dev-init` (Install tooling, copy env files)
    - `make dev-up` (Start API, worker, UI, and infrastructure services)
    - `docker compose -f infra/docker-compose.yml up --build -d` (Manually start services)
- **Lint:** (Assuming `ruff` is used based on common Python practices, add to `requirements-dev.txt` if not present)
    - `ruff check .`
    - `ruff format .`
- **Test:**
    - `pytest tests` (Run all tests)
    - `pytest tests/test_specific_module.py` (Run tests for a specific module)
    - `pytest tests/test_specific_module.py::test_specific_function` (Run a single test)

## Code Style Guidelines

- **Imports:** Follow standard Python import conventions (absolute imports preferred).
- **Formatting:** Use `black` for code formatting (configured via `pyproject.toml`).
- **Typing:** Utilize type hints extensively (Python 3.7+). Use `mypy` for static analysis.
- **Naming Conventions:**
    - Variables and functions: `snake_case`
    - Classes: `PascalCase`
    - Constants: `UPPER_SNAKE_CASE`
- **Directory Structure:** Organize code logically within `api/`, `worker/`, `ui/`, `ingest/` directories.
- **Error Handling:** Use custom exceptions where appropriate. Ensure exceptions are informative.
- **Configuration:** Managed via environment variables defined in `infra/.env`.

## Development Workflow

- Use `docker compose` for managing services.
- Utilize Makefile targets for common development tasks.
- Seed the database with sample data using `./scripts/dev_seed.sh`.
- Hot-reloading is enabled for API and UI development.

## Version Control

- Use Git for version control.
- Follow conventional commit messages.
- CI workflow in `.github/workflows/ci.yml` runs on every push/PR.
