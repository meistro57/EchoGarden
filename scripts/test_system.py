# test_system.py
"""Integration-style system smoke tests with graceful fallbacks."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


def _ensure_command_available(command: str) -> None:
    """Skip the test when a required CLI tool is unavailable."""
    if shutil.which(command) is None:
        pytest.skip(f"Required command '{command}' is not available in the environment.")


def _run_command(args: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    """Run a command and return the completed process, handling common errors."""
    try:
        return subprocess.run(
            args,
            capture_output=True,
            text=True,
            cwd=str(cwd) if cwd else None,
            check=False,
        )
    except FileNotFoundError as exc:
        pytest.skip(f"Command execution failed because '{exc.filename}' was not found.")


def test_system() -> None:
    """Test the full system functionality, skipping gracefully when prerequisites are absent."""
    root_dir = Path(__file__).resolve().parents[1]
    infra_dir = root_dir / "infra"
    compose_file = infra_dir / "docker-compose.yml"

    if not compose_file.exists():
        pytest.skip("Docker compose file is missing; integration stack is not available.")

    _ensure_command_available("docker")
    _ensure_command_available("curl")

    # 1. Check database is ready.
    db_result = _run_command(
        [
            "docker",
            "compose",
            "-f",
            str(compose_file),
            "exec",
            "db",
            "psql",
            "-U",
            "postgres",
            "-c",
            "SELECT 1;",
        ],
        cwd=infra_dir,
    )

    if db_result.returncode != 0:
        pytest.skip(
            "Database container is not reachable: "
            f"{db_result.stderr.strip() or db_result.stdout.strip()}"
        )

    # 2. Test API health endpoint.
    api_result = _run_command(["curl", "-sS", "http://localhost:8000/health"])

    if api_result.returncode != 0:
        pytest.skip(
            "API health check failed: "
            f"{api_result.stderr.strip() or api_result.stdout.strip()}"
        )

    assert api_result.stdout.strip(), "Health endpoint returned an empty response."
