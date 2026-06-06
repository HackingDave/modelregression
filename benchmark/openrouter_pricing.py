#!/usr/bin/env python3
"""
Fetch and normalize OpenRouter pricing for the website.

OpenRouter returns token prices as per-token decimal strings. The website shows
the operational unit people actually compare: dollars per 1M tokens.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from openrouter_client import fetch_models_catalog


SOURCE_URL = "https://openrouter.ai/api/v1/models?output_modalities=text"


def _to_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _per_million(value: Any) -> float | None:
    parsed = _to_float(value)
    if parsed is None:
        return None
    if parsed < 0:
        return None
    return round(parsed * 1_000_000, 6)


def pricing_entry_from_model(model: dict[str, Any]) -> dict[str, Any] | None:
    pricing = model.get("pricing") or {}
    prompt_per_m = _per_million(pricing.get("prompt"))
    completion_per_m = _per_million(pricing.get("completion"))
    cache_read_per_m = _per_million(pricing.get("input_cache_read"))

    if prompt_per_m is None and completion_per_m is None and cache_read_per_m is None:
        return None

    prompt = prompt_per_m or 0
    completion = completion_per_m or 0
    blended = round(prompt + completion, 6)

    return {
        "id": model.get("id"),
        "canonicalSlug": model.get("canonical_slug"),
        "name": model.get("name") or model.get("id"),
        "contextLength": model.get("context_length"),
        "promptPerMTok": prompt_per_m,
        "completionPerMTok": completion_per_m,
        "inputCacheReadPerMTok": cache_read_per_m,
        "blendedOneInOneOutPerM": blended,
        "isFree": prompt == 0 and completion == 0,
    }


def build_pricing_snapshot(timeout: int = 30) -> dict[str, Any]:
    catalog = fetch_models_catalog(timeout=timeout)
    entries = []
    for model in catalog:
        entry = pricing_entry_from_model(model)
        if entry and entry.get("id"):
            entries.append(entry)

    entries.sort(
        key=lambda item: (
            item["isFree"],
            item["blendedOneInOneOutPerM"],
            str(item["id"]),
        )
    )

    return {
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "source": SOURCE_URL,
        "modelCount": len(entries),
        "pricedModelCount": sum(1 for entry in entries if not entry["isFree"]),
        "freeModelCount": sum(1 for entry in entries if entry["isFree"]),
        "models": entries,
    }


def empty_pricing_snapshot(error: str | None = None) -> dict[str, Any]:
    snapshot: dict[str, Any] = {
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "source": SOURCE_URL,
        "modelCount": 0,
        "pricedModelCount": 0,
        "freeModelCount": 0,
        "models": [],
    }
    if error:
        snapshot["error"] = error
    return snapshot


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch OpenRouter pricing JSON")
    parser.add_argument(
        "--output",
        required=True,
        help="Output JSON path, e.g. public/data/openrouter-pricing.json",
    )
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args()

    snapshot = build_pricing_snapshot(timeout=args.timeout)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")
    print(
        f"Wrote {snapshot['modelCount']} OpenRouter price entries "
        f"to {output}"
    )


if __name__ == "__main__":
    main()
