"""
OpenRouter model manifest helpers.

Broad OpenRouter sweeps should be pinned in a manifest before benchmark runs.
Config import must stay offline and deterministic.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_MANIFEST_PATH = SCRIPT_DIR / "manifests" / "openrouter_models.json"

DEFAULT_OPEN_WEIGHT_PREFIXES = tuple(
    p.strip()
    for p in os.getenv(
        "OPENROUTER_OPEN_WEIGHT_PREFIXES",
        ",".join(
            [
                "meta-llama/",
                "mistralai/",
                "qwen/",
                "deepseek/",
                "google/gemma",
                "microsoft/",
                "nvidia/",
                "nousresearch/",
                "teknium/",
                "openchat/",
                "open-orca/",
                "allenai/",
                "01-ai/",
                "liquid/",
                "z-ai/",
                "moonshotai/",
            ]
        ),
    ).split(",")
    if p.strip()
)


def truthy_env(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def csv_env(name: str) -> list[str]:
    return [p.strip() for p in os.getenv(name, "").split(",") if p.strip()]


def slugify_model_id(model_id: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", model_id).strip("-").lower()
    return slug or "openrouter-model"


def model_color(model_id: str) -> str:
    palette = [
        "#14B8A6",
        "#F97316",
        "#3B82F6",
        "#EC4899",
        "#84CC16",
        "#A855F7",
        "#06B6D4",
        "#F59E0B",
        "#22C55E",
        "#EF4444",
    ]
    return palette[sum(ord(c) for c in model_id) % len(palette)]


def is_open_weight_candidate(
    model: dict[str, Any],
    prefixes: tuple[str, ...] = DEFAULT_OPEN_WEIGHT_PREFIXES,
    free_only: bool = False,
) -> bool:
    model_id = str(model.get("id", "")).lower()
    if not model_id:
        return False
    if free_only and not model_id.endswith(":free"):
        return False
    return model_id.startswith(prefixes)


def openrouter_model_config(
    model_id: str,
    name: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    slug = f"openrouter-{slugify_model_id(model_id)}"
    return {
        "id": slug,
        "cli": "openrouter",
        "cli_model": model_id,
        "name": name or f"OpenRouter: {model_id}",
        "slug": slug,
        "color": model_color(model_id),
        "icon": "cpu",
        "is_active": True,
        "metadata": metadata or {},
    }


def _manifest_models(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [m for m in payload if isinstance(m, dict)]
    if isinstance(payload, dict):
        models = payload.get("models", [])
        return [m for m in models if isinstance(m, dict)]
    return []


def load_openrouter_manifest(path: str | os.PathLike[str]) -> list[dict[str, Any]]:
    manifest_path = Path(path)
    with manifest_path.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    configs: list[dict[str, Any]] = []
    for item in _manifest_models(payload):
        model_id = str(item.get("id", "")).strip()
        if not model_id:
            continue
        metadata = dict(item)
        configs.append(
            openrouter_model_config(
                model_id,
                name=item.get("name") or f"OpenRouter: {model_id}",
                metadata=metadata,
            )
        )
    return configs


def load_openrouter_models_from_sources() -> list[dict[str, Any]]:
    """Load OpenRouter models from explicit IDs and pinned manifests only."""
    by_id: dict[str, dict[str, Any]] = {}

    manifest_path = os.getenv("OPENROUTER_MANIFEST")
    if manifest_path is None and DEFAULT_MANIFEST_PATH.exists():
        manifest_path = str(DEFAULT_MANIFEST_PATH)

    if manifest_path:
        for cfg in load_openrouter_manifest(manifest_path):
            by_id[cfg["cli_model"]] = cfg

    for model_id in csv_env("OPENROUTER_MODEL_IDS"):
        by_id[model_id] = openrouter_model_config(model_id)

    return list(by_id.values())
