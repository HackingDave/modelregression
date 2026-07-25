import json
from pathlib import Path
import subprocess
import sys

BENCHMARK_DIR = Path(__file__).resolve().parent
if str(BENCHMARK_DIR) not in sys.path:
    sys.path.insert(0, str(BENCHMARK_DIR))

from model_resolver import (
    model_display_name,
    model_storage_id,
    resolve_codex_frontier_model,
    resolve_grok_default_model,
    resolve_with_override,
)


def _result(stdout: str = "", returncode: int = 0) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess([], returncode, stdout=stdout, stderr="")


def test_codex_resolver_prefers_catalog_entry_marked_latest_frontier():
    catalog = {
        "models": [
            {
                "slug": "gpt-older",
                "visibility": "list",
                "priority": 0,
                "description": "Previous model",
            },
            {
                "slug": "gpt-current-sol",
                "visibility": "list",
                "priority": 4,
                "description": "Latest frontier agentic coding model.",
            },
            {
                "slug": "gpt-hidden",
                "visibility": "hide",
                "priority": 1,
                "description": "Latest frontier model",
            },
        ]
    }

    resolved = resolve_codex_frontier_model(
        runner=lambda *_args, **_kwargs: _result(json.dumps(catalog))
    )

    assert resolved == "gpt-current-sol"


def test_codex_resolver_falls_back_when_catalog_is_unavailable():
    resolved = resolve_codex_frontier_model(
        fallback="gpt-known-good",
        runner=lambda *_args, **_kwargs: _result("not json"),
    )

    assert resolved == "gpt-known-good"


def test_grok_resolver_uses_cli_default_model():
    resolved = resolve_grok_default_model(
        runner=lambda *_args, **_kwargs: _result(
            "Available models:\n- grok-4.5\nDefault model: grok-4.5\n"
        )
    )

    assert resolved == "grok-4.5"


def test_environment_override_skips_runtime_discovery():
    called = False

    def resolver() -> str:
        nonlocal called
        called = True
        return "runtime-model"

    resolved = resolve_with_override(
        "MODELREGRESSION_CODEX_MODEL",
        {"MODELREGRESSION_CODEX_MODEL": " pinned-model "},
        resolver,
    )

    assert resolved == "pinned-model"
    assert called is False


def test_model_names_and_storage_ids_are_human_readable():
    assert model_storage_id("gpt-5.6-sol") == "gpt-5-6-sol"
    assert model_display_name("gpt-5.6-sol") == "GPT-5.6 Sol"
    assert model_display_name("grok-4.5") == "Grok 4.5"
