# scripts/startup.py
"""Comprehensive startup script for EchoGarden services.

This script prepares environment configuration, bootstraps Docker services,
waits for critical dependencies, initializes the database schema, and verifies
that the API and UI are reachable. It is designed for local development and
one-command onboarding.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parent.parent
INFRA_DIR = REPO_ROOT / "infra"
DOCKER_COMPOSE_FILE = INFRA_DIR / "docker-compose.yml"
ENV_FILE = INFRA_DIR / ".env"
ENV_EXAMPLE_FILE = INFRA_DIR / ".env.example"
INIT_SQL_FILE = INFRA_DIR / "init_db.sql"


class StartupError(RuntimeError):
    """Raised when the startup flow fails."""


def log(message: str) -> None:
    """Lightweight logger with timestamped output."""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")


def run_command(command: Iterable[str], *, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    """Run a subprocess command with optional working directory and error handling."""
    result = subprocess.run(command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if check and result.returncode != 0:
        raise StartupError(f"Command failed: {' '.join(command)}\nOutput: {result.stdout.strip()}")
    return result


def ensure_env_file() -> None:
    """Create the infra/.env file if it does not already exist."""
    if ENV_FILE.exists():
        log("Existing infra/.env detected; leaving it untouched.")
        return
    if not ENV_EXAMPLE_FILE.exists():
        raise StartupError("Missing infra/.env.example; cannot bootstrap configuration.")
    shutil.copy(ENV_EXAMPLE_FILE, ENV_FILE)
    log("Created infra/.env from example. Please update API keys after startup if needed.")


def check_prerequisites() -> None:
    """Verify Docker and Docker Compose availability."""
    try:
        run_command(["docker", "--version"], check=True)
        run_command(["docker", "compose", "version"], check=True)
    except FileNotFoundError as exc:
        raise StartupError("Docker is not installed or not on PATH.") from exc


def start_services(build: bool) -> None:
    """Start all Docker services defined in infra/docker-compose.yml."""
    command = ["docker", "compose", "-f", str(DOCKER_COMPOSE_FILE), "up", "-d"]
    if build:
        command.append("--build")
    log("Starting Docker services (db, redis, minio, api, worker, ui)...")
    result = run_command(command)
    if result.stdout:
        log(result.stdout.strip())


def wait_for_database(timeout: int = 90) -> None:
    """Wait for the PostgreSQL service to become ready."""
    log("Waiting for PostgreSQL to accept connections...")
    deadline = time.time() + timeout
    probe_cmd = [
        "docker",
        "compose",
        "-f",
        str(DOCKER_COMPOSE_FILE),
        "exec",
        "-T",
        "db",
        "pg_isready",
        "-U",
        "postgres",
    ]
    while time.time() < deadline:
        try:
            result = run_command(probe_cmd, check=False)
            if result.returncode == 0:
                log("PostgreSQL is ready.")
                return
        except StartupError:
            # Container may not be up yet; keep waiting.
            pass
        time.sleep(3)
    raise StartupError("Timed out waiting for PostgreSQL to become ready.")


def initialize_database() -> None:
    """Apply the initial database schema using init_db.sql."""
    if not INIT_SQL_FILE.exists():
        raise StartupError("Missing infra/init_db.sql; cannot initialize database schema.")
    log("Applying database schema (idempotent)...")
    apply_cmd = [
        "docker",
        "compose",
        "-f",
        str(DOCKER_COMPOSE_FILE),
        "exec",
        "-T",
        "db",
        "psql",
        "-U",
        "postgres",
    ]
    sql_content = INIT_SQL_FILE.read_text(encoding="utf-8")
    result = subprocess.run(apply_cmd, input=sql_content, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if result.returncode != 0:
        raise StartupError(f"Failed to apply database schema. Output: {result.stdout.strip()}")
    log("Database schema ensured.")


def wait_for_http(name: str, url: str, timeout: int = 120) -> None:
    """Poll an HTTP endpoint until it returns a successful status code."""
    log(f"Waiting for {name} at {url} ...")
    deadline = time.time() + timeout
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                if 200 <= response.status < 500:  # Accept 4xx for UI build splash, etc.
                    log(f"{name} responded with HTTP {response.status}.")
                    return
        except (urllib.error.URLError, urllib.error.HTTPError) as exc:  # pragma: no cover - network dependent
            last_error = exc
        time.sleep(5)
    raise StartupError(f"Timed out waiting for {name} ({url}). Last error: {last_error}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Boot EchoGarden with one command.")
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Skip image rebuild; start existing containers only.",
    )
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000/health",
        help="Health endpoint for the API service.",
    )
    parser.add_argument(
        "--ui-url",
        default="http://localhost:3000",
        help="Base URL for the UI service to verify availability.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        ensure_env_file()
        check_prerequisites()
        start_services(build=not args.skip_build)
        wait_for_database()
        initialize_database()
        wait_for_http("API", args.api_url)
        wait_for_http("UI", args.ui_url)
    except StartupError as error:
        log(f"Startup failed: {error}")
        return 1

    log("EchoGarden is up and blooming. 🚀")
    log("Resources:")
    log("  API Docs:      http://localhost:8000/docs")
    log("  Web UI:        http://localhost:3000")
    log("  MinIO Console: http://localhost:9001")
    log("Use 'docker compose -f infra/docker-compose.yml ps' to inspect service status.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
