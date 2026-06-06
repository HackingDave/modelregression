#!/usr/bin/env python3
"""
Generate a pinned OpenRouter model manifest.

This command is the supported way to prepare broad OpenRouter sweeps. Benchmark
configuration reads the manifest later without doing network discovery at import
time.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from openrouter_client import fetch_models_catalog
from openrouter_models import (
    DEFAULT_MANIFEST_PATH,
    DEFAULT_OPEN_WEIGHT_PREFIXES,
    is_open_weight_candidate,
)


def _model_entry(model: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "id",
        "canonical_slug",
        "name",
        "created",
        "description",
        "context_length",
        "architecture",
        "pricing",
        "top_provider",
        "per_request_limits",
        "supported_parameters",
        "default_parameters",
        "expiration_date",
    ]
    return {k: model.get(k) for k in keys if k in model}


def build_manifest(args: argparse.Namespace) -> dict[str, Any]:
    catalog = fetch_models_catalog(timeout=args.timeout)
    by_id = {str(m.get("id", "")): m for m in catalog if m.get("id")}

    selected: list[dict[str, Any]] = []
    explicit = [m.strip() for m in args.model if m.strip()]
    if explicit:
        for model_id in explicit:
            selected.append(_model_entry(by_id.get(model_id, {"id": model_id, "name": model_id})))
    else:
        prefixes = tuple(args.prefix or DEFAULT_OPEN_WEIGHT_PREFIXES)
        selected = [
            _model_entry(m)
            for m in catalog
            if is_open_weight_candidate(m, prefixes=prefixes, free_only=args.free_only)
        ]
        selected.sort(key=lambda m: str(m.get("id", "")))

    if args.limit > 0:
        selected = selected[: args.limit]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "https://openrouter.ai/api/v1/models?output_modalities=text",
        "filters": {
            "explicit_models": explicit,
            "prefixes": list(args.prefix or DEFAULT_OPEN_WEIGHT_PREFIXES),
            "free_only": args.free_only,
            "limit": args.limit,
        },
        "model_count": len(selected),
        "models": selected,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate an OpenRouter model manifest")
    parser.add_argument(
        "--output",
        default=str(DEFAULT_MANIFEST_PATH),
        help="Manifest path to write (default: benchmark/manifests/openrouter_models.json)",
    )
    parser.add_argument(
        "--model",
        action="append",
        default=[],
        help="Explicit OpenRouter model ID to include. Repeat for multiple models.",
    )
    parser.add_argument(
        "--prefix",
        action="append",
        default=[],
        help="Open-weight candidate prefix to include when --model is omitted.",
    )
    parser.add_argument("--limit", type=int, default=0, help="Maximum selected models; 0 means no limit")
    parser.add_argument("--free-only", action="store_true", help="Only include model IDs ending in :free")
    parser.add_argument("--timeout", type=int, default=30, help="Catalog request timeout in seconds")
    args = parser.parse_args()

    manifest = build_manifest(args)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {manifest['model_count']} model(s) to {output}")


if __name__ == "__main__":
    main()
