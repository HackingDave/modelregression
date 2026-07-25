"""Resolve the current frontier model exposed by each benchmark CLI.

The benchmark intentionally follows rolling CLI channels instead of pinning
provider snapshots. Environment overrides remain available for incident
response and reproducible one-off runs.
"""

from __future__ import annotations

import json
import re
import subprocess
from collections.abc import Callable, Mapping, Sequence


CommandRunner = Callable[..., subprocess.CompletedProcess]


def _run_command(
    command: Sequence[str],
    *,
    runner: CommandRunner = subprocess.run,
) -> subprocess.CompletedProcess:
    """Run a small read-only CLI discovery command with a bounded timeout."""
    return runner(
        list(command),
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )


def resolve_codex_frontier_model(
    fallback: str = "gpt-5.6-sol",
    *,
    runner: CommandRunner = subprocess.run,
) -> str:
    """Return Codex's highest-priority visible frontier model.

    Modern Codex releases expose their model catalog as JSON. Prefer the entry
    explicitly described as the latest frontier model, then fall back to the
    lowest numeric catalog priority. A known-good fallback keeps configuration
    importable when Codex is absent or temporarily unhealthy.
    """
    try:
        result = _run_command(("codex", "debug", "models"), runner=runner)
        if result.returncode != 0:
            return fallback
        payload = json.loads(result.stdout)
        models = [
            model
            for model in payload.get("models", [])
            if isinstance(model, dict)
            and model.get("visibility") == "list"
            and isinstance(model.get("slug"), str)
        ]
        if not models:
            return fallback

        def priority(model: dict) -> int:
            value = model.get("priority")
            return value if isinstance(value, int) else 1_000_000

        frontier = [
            model
            for model in models
            if "latest frontier" in str(model.get("description", "")).lower()
        ]
        selected = min(frontier or models, key=priority)
        return selected["slug"]
    except (
        AttributeError,
        FileNotFoundError,
        json.JSONDecodeError,
        KeyError,
        OSError,
        subprocess.SubprocessError,
        TypeError,
    ):
        return fallback


def resolve_grok_default_model(
    fallback: str = "grok-4.5",
    *,
    runner: CommandRunner = subprocess.run,
) -> str:
    """Return the model marked as default by the installed Grok CLI."""
    try:
        result = _run_command(("grok", "models"), runner=runner)
        if result.returncode != 0:
            return fallback
        match = re.search(r"^Default model:\s*(\S+)\s*$", result.stdout, re.MULTILINE)
        return match.group(1) if match else fallback
    except (FileNotFoundError, OSError, subprocess.SubprocessError, TypeError):
        return fallback


def resolve_with_override(
    env_var: str,
    environment: Mapping[str, str],
    resolver: Callable[[], str],
) -> str:
    """Use a non-empty environment override, otherwise call the resolver."""
    override = environment.get(env_var, "").strip()
    return override or resolver()


def model_storage_id(model: str) -> str:
    """Convert a provider model slug into the repository's stable file/id form."""
    return model.replace(".", "-")


def model_display_name(model: str) -> str:
    """Create the human-readable names used by the current provider catalog."""
    if model.startswith("gpt-"):
        parts = model.split("-")
        version = parts[1] if len(parts) > 1 else model
        tier = " ".join(part.title() for part in parts[2:])
        return f"GPT-{version}{f' {tier}' if tier else ''}"
    if model.startswith("grok-"):
        return f"Grok {model.removeprefix('grok-')}"
    return model
