# README.md
# EchoGarden

![EchoGarden Logo](https://img.shields.io/badge/EchoGarden-Growing%20Memories-4CAF50?style=for-the-badge)
[![CI](https://github.com/meistro57/EchoGarden/actions/workflows/ci.yml/badge.svg?style=for-the-badge)](https://github.com/meistro57/EchoGarden/actions/workflows/ci.yml)
[![Tests](https://img.shields.io/badge/tests-passing-4CAF50?style=for-the-badge&logo=pytest)](tests/)
[![Python](https://img.shields.io/badge/python-3.11%2B-3776AB?style=for-the-badge&logo=python)](requirements-dev.txt)

EchoGarden is a research environment for building rich memory and search experiences from large ChatGPT exports. It stitches together an ingestion pipeline, a FastAPI-powered service layer, Celery workers, and a modern web UI so that you can explore conversational datasets with semantic and temporal context.

> "Cultivate conversations, prune the noise, and harvest insights." — the EchoGarden way.

## Contents

- [Highlights](#highlights)
- [Quick start](#quick-start)
- [Local development](#local-development)
- [Testing](#testing)
- [Project layout](#project-layout)
- [CI with GitHub Actions](#ci-with-github-actions)
- [Troubleshooting](#troubleshooting)

## Highlights

- 🌿 **Curated ingestion pipeline** that normalises ChatGPT exports and enriches them with semantic metadata.
- 🔍 **High-fidelity search** powered by embeddings, temporal filters, and contextual summaries.
- ⚙️ **Composable architecture** spanning FastAPI, Celery, and a Next.js front-end.
- 🧪 **Testing-first mindset** with pytest suites and smoke scenarios for ingestion.
- 🧭 **Guided developer experience** via Makefile targets, scripts, and containerised services.

## Quick start

The quickest way to bring up the full stack is via the Makefile wrapper. This bootstraps Python and JavaScript dependencies, provisions the Docker services, and starts the developer processes.

```bash
make dev-init      # one-off: install tooling, copy env files
make dev-up        # start API, worker, UI, and infrastructure services
```

Prefer to run the commands manually? The following sequence mirrors the Make targets without hiding any steps:

```bash
git clone https://github.com/meistro57/EchoGarden.git
cd EchoGarden
cp infra/.env.example infra/.env
docker compose -f infra/docker-compose.yml up --build -d
./scripts/dev_start.sh
```

## Local development

1. **Infrastructure:** `docker compose -f infra/docker-compose.yml up -d db redis minio`
2. **Seed data:** `./scripts/dev_seed.sh`
3. **API:** `cd api && python -m uvicorn main:app --reload`
4. **Worker:** `cd worker && celery -A tasks worker --loglevel=info`
5. **UI:** `cd ui && npm run dev`

Useful environment variables live in `infra/.env`. The defaults are safe for a local sandbox; override them if you need to point at external services.

### Handy scripts

- `./scripts/dev_start.sh` — orchestrates the API, worker, and UI for local hacking sessions.
- `./scripts/dev_seed.sh` — hydrates PostgreSQL with sample conversations.
- `./scripts/test_system.py` — smoke tests the ingestion workflow end to end.

## Testing

Automated tests live under `tests/` and focus on input normalisation and PII redaction at present. They are executable locally and in CI via `pytest`.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest tests
```

Add `-k pattern` to run a subset of the suite or `-vv` for verbose output when diagnosing failures.

End-to-end smoke tests for the ingestion pipeline remain available:

```bash
python scripts/test_system.py
python ingest/import_chatgpt_export.py --owner-id your_user path/to/conversations.zip
```

## Project layout

| Path          | Description                                                 |
|---------------|-------------------------------------------------------------|
| `api/`        | FastAPI application, including service utilities.           |
| `worker/`     | Celery worker processes and scheduled jobs.                 |
| `ui/`         | Front-end (Next.js) application for browsing conversations. |
| `infra/`      | Docker Compose stack, PostgreSQL bootstrap scripts, envs.   |
| `ingest/`     | One-off ingestion scripts and supporting libraries.         |
| `schemas/`    | SQL schemas and migration helpers.                          |
| `tests/`      | Pytest-based unit tests.                                    |

## CI with GitHub Actions

Continuous integration runs on every push and pull request. The workflow in `.github/workflows/ci.yml` installs dependencies from `requirements-dev.txt` and executes the automated test suite. Extend this workflow as new services or languages gain coverage.

To try the workflow locally you can install [act](https://github.com/nektos/act) and run `act -j tests` to execute the same steps in a container.

## Troubleshooting

- **Docker refuses to start MinIO:** Ensure port `9000` is free and that the host has at least 4GB RAM available.
- **`psycopg2` build issues on macOS:** Install PostgreSQL via Homebrew (`brew install postgresql`) to provide the required headers.
- **`pytest` cannot import the API package:** Activate the virtual environment and run tests from the repository root so that `api/` is discoverable.
- **Need to reset MinIO or the database?** Run `make dev-down` followed by `make dev-up` to recreate containers with clean volumes.

