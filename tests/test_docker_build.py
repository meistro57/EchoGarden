# tests/test_docker_build.py
"""Validate Docker build contexts and runtime commands for containerised services."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pytest
import yaml


def _project_root() -> Path:
    """Return the repository root path with a safety assertion."""
    root = Path(__file__).resolve().parents[1]
    if not root.exists():  # pragma: no cover - defensive guard
        raise AssertionError("Project root could not be resolved.")
    return root


def _compose_services() -> tuple[dict, Path]:
    """Load the docker-compose configuration and return services alongside the path."""
    compose_path = _project_root() / "infra" / "docker-compose.yml"
    if not compose_path.exists():
        raise AssertionError("docker-compose.yml is missing; Docker stack cannot be validated.")

    with compose_path.open(encoding="utf-8") as handle:
        compose_data = yaml.safe_load(handle)

    services = compose_data.get("services") if isinstance(compose_data, dict) else None
    if not services:
        raise AssertionError("No services section found in docker-compose.yml.")

    return services, compose_path


def _extract_instructions(dockerfile_path: Path) -> list[str]:
    """Extract top-level Dockerfile instructions ignoring comments and blank lines."""
    if not dockerfile_path.exists():
        raise AssertionError(f"Expected Dockerfile at {dockerfile_path} to exist.")

    instructions: list[str] = []
    with dockerfile_path.open(encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            instructions.append(line.split()[0].upper())
    return instructions


def _iter_build_contexts(services: dict, compose_path: Path) -> Iterable[tuple[str, Path]]:
    """Yield service names and resolved build directories from the compose configuration."""
    compose_dir = compose_path.parent
    for service_name, config in services.items():
        build_context = config.get("build") if isinstance(config, dict) else None
        if not build_context:
            continue
        context_path = (compose_dir / build_context).resolve()
        yield service_name, context_path


@pytest.mark.parametrize(
    "service_name,context_path",
    list(_iter_build_contexts(*_compose_services())),
)
def test_compose_build_context_has_dockerfile(service_name: str, context_path: Path) -> None:
    """Ensure each service build context includes a Dockerfile with a base image declaration."""
    dockerfile_path = context_path / "Dockerfile"
    instructions = _extract_instructions(dockerfile_path)

    assert instructions, f"Dockerfile for service '{service_name}' is empty."
    assert (
        instructions[0] == "FROM"
    ), f"Dockerfile for service '{service_name}' must start with a FROM instruction."


@pytest.mark.parametrize(
    "dockerfile_path",
    sorted(_project_root().glob("*/Dockerfile")),
)
def test_dockerfile_defines_runtime_command(dockerfile_path: Path) -> None:
    """Verify every Dockerfile defines how the container will start (CMD or ENTRYPOINT)."""
    instructions = _extract_instructions(dockerfile_path)
    assert any(
        instruction in {"CMD", "ENTRYPOINT"} for instruction in instructions
    ), f"Dockerfile '{dockerfile_path}' must define CMD or ENTRYPOINT to run the service."


@pytest.mark.parametrize(
    "service_name,context_path",
    list(_iter_build_contexts(*_compose_services())),
)
def test_build_context_contains_expected_runtime_artifacts(service_name: str, context_path: Path) -> None:
    """Check runtime-critical files exist within each build context to avoid build-time surprises."""
    required_files = {
        "api": ["requirements.txt", "main.py"],
        "worker": ["requirements.txt", "tasks.py"],
        "ui": ["package.json", "package-lock.json"],
    }
    expectations = required_files.get(service_name, [])
    missing = [file_name for file_name in expectations if not (context_path / file_name).exists()]
    assert not missing, (
        "Build context for service "
        f"'{service_name}' is missing required files: {', '.join(missing)}"
    )
