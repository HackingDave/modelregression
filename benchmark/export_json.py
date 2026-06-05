#!/usr/bin/env python3
"""
Export benchmark data from SQLite to JSON files for the Next.js website.

Reads benchmarks.db and generates the complete set of static JSON data files
matching the exact structure consumed by the frontend at build time:

  - latest.json                            (most recent benchmark run)
  - synopsis.json                          (best model per day/week/month)
  - models/{slug}.json                     (per-model detail + history)
  - categories/{slug}.json                 (per-category detail + history)
  - trends/daily.json|weekly|monthly|yearly (composite trend lines)
  - regressions.json                       (active + recently resolved)
  - outages.json                           (current + history + uptime)
  - evidence/{run-label}/{test-id}.json    (full test evidence, last 30 days)

Usage:
  python export_json.py                           # defaults
  python export_json.py --output ../public/data   # explicit output dir
  python export_json.py --db data/benchmarks.db   # explicit DB path
"""

import argparse
import json
import logging
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone

# Allow running from the benchmark directory or anywhere
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
import db as database

logger = logging.getLogger(__name__)

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _iso(dt_str: str | None) -> str | None:
    """Normalise a datetime string to ISO 8601 with .000Z suffix.

    Handles the various formats SQLite may store:
      2026-06-04T02:00:00+00:00
      2026-06-04T02:00:00.123456+00:00
      2026-06-04 02:00:00
      2026-06-04T02:00:00.000Z  (already correct)
    """
    if not dt_str:
        return None
    if dt_str.endswith(".000Z"):
        return dt_str  # already in target format
    # Try standard fromisoformat first (handles +00:00, Z, etc.)
    for attempt in (dt_str, dt_str.replace("Z", "+00:00")):
        try:
            dt = datetime.fromisoformat(attempt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.strftime("%Y-%m-%dT%H:%M:%S") + ".000Z"
        except (ValueError, TypeError):
            continue
    # Last resort: strip everything after seconds and append .000Z
    base = dt_str.split(".")[0].split("+")[0].replace(" ", "T")
    return base + ".000Z"


def _round_score(val) -> float | int | None:
    """Round a score to one decimal, returning int when the decimal is .0.

    The seed JSON files use 92 (not 92.0) but 92.5 stays as-is.
    """
    if val is None:
        return None
    r = round(float(val), 1)
    return int(r) if r == int(r) else r


def _run_label(run: dict) -> str:
    """Derive a human-friendly run ID like 'run-2026-06-04-night'."""
    started = run.get("started_at", "")
    schedule = run.get("schedule", "night")
    try:
        dt = datetime.fromisoformat(started.replace("Z", "+00:00"))
        return f"run-{dt.strftime('%Y-%m-%d')}-{schedule}"
    except (ValueError, AttributeError):
        return f"run-unknown-{schedule}"


def _display_test_id(test_id: str) -> str:
    """Map internal test IDs to display IDs (cth-* -> th-*)."""
    return config.display_test_id(test_id)


def _write_json(path: str, data) -> None:
    """Write *data* as pretty-printed JSON, creating parent dirs as needed."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    logger.debug("Wrote %s", path)


# ---------------------------------------------------------------------------
# latest.json
# ---------------------------------------------------------------------------

def _get_latest_run_for_model(conn, model_id: str) -> dict | None:
    """Find the most recent completed run that has results for this model."""
    row = conn.execute(
        """SELECT br.* FROM benchmark_runs br
           JOIN model_run_scores mrs ON mrs.run_id = br.id
           WHERE mrs.model_id = ?
             AND br.status IN ('completed', 'completed_with_errors')
           ORDER BY br.started_at DESC LIMIT 1""",
        (model_id,),
    ).fetchone()
    return dict(row) if row else None


def export_latest(conn, output_dir: str) -> None:
    """Most recent data per model, composited across runs.

    When single-model runs exist (e.g. --model grok), each model's data
    is pulled from its own most recent run so partial runs don't hide
    other models from the dashboard.
    """
    latest_run = database.get_latest_run(conn)
    if not latest_run:
        _write_json(os.path.join(output_dir, "latest.json"), {
            "runId": None, "startedAt": None, "completedAt": None,
            "schedule": None, "models": {},
        })
        return

    models_data = {}
    all_composites = []

    for mcfg in config.MODELS:
        mid = mcfg["id"]
        slug = mcfg["slug"]
        model_run = _get_latest_run_for_model(conn, mid)
        if not model_run:
            continue

        run_id = model_run["id"]

        mc = conn.execute(
            "SELECT composite_score, rank FROM model_run_scores WHERE run_id = ? AND model_id = ?",
            (run_id, mid),
        ).fetchone()
        if not mc:
            continue

        all_composites.append((slug, mc["composite_score"]))

        cat_rows = conn.execute(
            """SELECT rs.*, c.slug as category_slug
               FROM run_scores rs
               JOIN categories c ON rs.category_id = c.id
               WHERE rs.run_id = ? AND rs.model_id = ?""",
            (run_id, mid),
        ).fetchall()

        test_rows = conn.execute(
            """SELECT tr.*, t.name as test_name, c.slug as category_slug
               FROM test_results tr
               JOIN tests t ON tr.test_id = t.id
               JOIN categories c ON tr.category_id = c.id
               WHERE tr.run_id = ? AND tr.model_id = ? AND tr.score IS NOT NULL""",
            (run_id, mid),
        ).fetchall()

        tests_by_cat = defaultdict(list)
        for tr in test_rows:
            tests_by_cat[tr["category_slug"]].append({
                "testId": _display_test_id(tr["test_id"]),
                "name": tr["test_name"],
                "score": _round_score(tr["score"]),
                "latencyMs": tr["latency_ms"],
            })

        categories = {}
        for cs in cat_rows:
            cslug = cs["category_slug"]
            categories[cslug] = {
                "avgScore": _round_score(cs["avg_score"]),
                "testCount": cs["test_count"],
                "tests": tests_by_cat.get(cslug, []),
            }

        models_data[slug] = {
            "compositeScore": _round_score(mc["composite_score"]),
            "rank": mc["rank"],
            "categories": categories,
        }

    # Recompute ranks across all models for the composite view
    all_composites.sort(key=lambda x: x[1] or 0, reverse=True)
    for rank, (slug, _) in enumerate(all_composites, 1):
        if slug in models_data:
            models_data[slug]["rank"] = rank

    _write_json(os.path.join(output_dir, "latest.json"), {
        "runId": _run_label(latest_run),
        "startedAt": _iso(latest_run["started_at"]),
        "completedAt": _iso(latest_run.get("completed_at")),
        "schedule": latest_run.get("schedule"),
        "models": models_data,
    })


# ---------------------------------------------------------------------------
# synopsis.json
# ---------------------------------------------------------------------------

def export_synopsis(conn, output_dir: str) -> None:
    """Best model per day / week / month windows."""
    now = datetime.now(timezone.utc)

    def _best_in_period(days: int) -> dict:
        cutoff = (now - timedelta(days=days)).isoformat()
        row = conn.execute(
            """SELECT m.slug, m.name, AVG(mrs.composite_score) as avg_score
               FROM model_run_scores mrs
               JOIN models m ON mrs.model_id = m.id
               JOIN benchmark_runs br ON mrs.run_id = br.id
               WHERE br.started_at >= ?
                 AND br.status IN ('completed', 'completed_with_errors')
               GROUP BY m.slug
               ORDER BY avg_score DESC LIMIT 1""",
            (cutoff,),
        ).fetchone()
        if not row:
            return {"modelId": None, "name": None, "score": None, "change": 0}

        # Change vs previous identical window
        prev_cutoff = (now - timedelta(days=days * 2)).isoformat()
        prev = conn.execute(
            """SELECT AVG(mrs.composite_score) as avg_score
               FROM model_run_scores mrs
               JOIN models m ON mrs.model_id = m.id
               JOIN benchmark_runs br ON mrs.run_id = br.id
               WHERE m.slug = ? AND br.started_at >= ? AND br.started_at < ?
                 AND br.status IN ('completed', 'completed_with_errors')""",
            (row["slug"], prev_cutoff, cutoff),
        ).fetchone()
        change = 0
        if prev and prev["avg_score"]:
            change = round(row["avg_score"] - prev["avg_score"], 1)

        return {
            "modelId": row["slug"],
            "name": row["name"],
            "score": _round_score(row["avg_score"]),
            "change": change,
        }

    # Use latest completed_at as updatedAt
    latest = database.get_latest_run(conn)
    updated_at = _iso(latest["completed_at"]) if latest and latest.get("completed_at") else _iso(now.isoformat())

    _write_json(os.path.join(output_dir, "synopsis.json"), {
        "day": _best_in_period(1),
        "week": _best_in_period(7),
        "month": _best_in_period(30),
        "updatedAt": updated_at,
    })


# ---------------------------------------------------------------------------
# models/{slug}.json
# ---------------------------------------------------------------------------

def export_models(conn, output_dir: str) -> None:
    """Per-model detail page data with full history, regressions, outages."""
    models_dir = os.path.join(output_dir, "models")

    all_runs = conn.execute(
        """SELECT * FROM benchmark_runs
           WHERE status IN ('completed', 'completed_with_errors')
           ORDER BY started_at ASC"""
    ).fetchall()

    # First pass: collect current data and composites for cross-model ranking
    model_results = {}
    all_composites = []

    for mcfg in config.MODELS:
        mid = mcfg["id"]
        slug = mcfg["slug"]

        model_meta = {
            "id": mid,
            "provider": mcfg["cli"],
            "name": mcfg["name"],
            "slug": slug,
            "color": mcfg["color"],
            "icon": mcfg.get("icon", "cpu"),
        }

        # --- current (from this model's latest run) ---
        model_run = _get_latest_run_for_model(conn, mid)
        current = _model_current(conn, model_run, mid) if model_run else {
            "compositeScore": None, "rank": None, "categories": {},
        }

        if current["compositeScore"] is not None:
            all_composites.append((slug, current["compositeScore"]))

        # --- history (ALL completed runs) ---
        history = []
        for run in all_runs:
            run = dict(run)
            entry = _model_history_entry(conn, run, mid)
            if entry:
                history.append(entry)

        # --- regressions ---
        reg_rows = conn.execute(
            """SELECT r.*, c.name as category_name, c.slug as category_slug
               FROM regressions r
               LEFT JOIN categories c ON r.category_id = c.id
               WHERE r.model_id = ?
               ORDER BY r.detected_at DESC""",
            (mid,),
        ).fetchall()
        regressions = []
        for reg in reg_rows:
            regressions.append({
                "id": reg["id"],
                "categoryId": reg["category_slug"],
                "categoryName": reg["category_name"],
                "detectedAt": _iso(reg["detected_at"]),
                "previousAvg": _round_score(reg["previous_avg"]),
                "currentScore": _round_score(reg["current_score"]),
                "dropPct": _round_score(reg["drop_pct"]),
                "severity": reg["severity"],
                "resolvedAt": _iso(reg["resolved_at"]),
            })

        # --- outages ---
        out_rows = conn.execute(
            "SELECT * FROM outages WHERE model_id = ? ORDER BY started_at DESC",
            (mid,),
        ).fetchall()
        outages = []
        for o in out_rows:
            outages.append({
                "id": o["id"],
                "startedAt": _iso(o["started_at"]),
                "endedAt": _iso(o["ended_at"]),
                "errorType": o["error_type"],
                "httpStatus": o["http_status"],
            })

        model_results[slug] = {
            "model": model_meta,
            "current": current,
            "history": history,
            "regressions": regressions,
            "outages": outages,
        }

    # Recompute cross-model ranks
    all_composites.sort(key=lambda x: x[1], reverse=True)
    for rank, (slug, _) in enumerate(all_composites, 1):
        model_results[slug]["current"]["rank"] = rank

    for slug, data in model_results.items():
        _write_json(os.path.join(models_dir, f"{slug}.json"), data)


def _model_current(conn, run: dict, model_id: str) -> dict:
    """Build the 'current' block for a model page from the given run."""
    run_id = run["id"]
    mc = conn.execute(
        "SELECT composite_score, rank FROM model_run_scores WHERE run_id = ? AND model_id = ?",
        (run_id, model_id),
    ).fetchone()
    if not mc:
        return {"compositeScore": None, "rank": None, "categories": {}}

    # Category aggregates
    cat_rows = conn.execute(
        """SELECT rs.*, c.slug as category_slug
           FROM run_scores rs
           JOIN categories c ON rs.category_id = c.id
           WHERE rs.run_id = ? AND rs.model_id = ?""",
        (run_id, model_id),
    ).fetchall()

    # Test results
    test_rows = conn.execute(
        """SELECT tr.*, t.name as test_name, c.slug as category_slug
           FROM test_results tr
           JOIN tests t ON tr.test_id = t.id
           JOIN categories c ON tr.category_id = c.id
           WHERE tr.run_id = ? AND tr.model_id = ? AND tr.score IS NOT NULL""",
        (run_id, model_id),
    ).fetchall()

    tests_by_cat = defaultdict(list)
    for tr in test_rows:
        tests_by_cat[tr["category_slug"]].append({
            "testId": _display_test_id(tr["test_id"]),
            "name": tr["test_name"],
            "score": _round_score(tr["score"]),
            "latencyMs": tr["latency_ms"],
        })

    categories = {}
    for cs in cat_rows:
        cslug = cs["category_slug"]
        categories[cslug] = {
            "avgScore": _round_score(cs["avg_score"]),
            "testCount": cs["test_count"],
            "tests": tests_by_cat.get(cslug, []),
        }

    return {
        "compositeScore": _round_score(mc["composite_score"]),
        "rank": mc["rank"],
        "categories": categories,
    }


def _model_history_entry(conn, run: dict, model_id: str) -> dict | None:
    """Build one history entry {timestamp, compositeScore, categories: {...}}."""
    mc = conn.execute(
        "SELECT composite_score FROM model_run_scores WHERE run_id = ? AND model_id = ?",
        (run["id"], model_id),
    ).fetchone()
    if not mc:
        return None

    cat_rows = conn.execute(
        """SELECT rs.avg_score, c.slug as category_slug
           FROM run_scores rs
           JOIN categories c ON rs.category_id = c.id
           WHERE rs.run_id = ? AND rs.model_id = ?""",
        (run["id"], model_id),
    ).fetchall()

    cats = {cs["category_slug"]: _round_score(cs["avg_score"]) for cs in cat_rows}

    return {
        "timestamp": _iso(run["started_at"]),
        "compositeScore": _round_score(mc["composite_score"]),
        "categories": cats,
    }


# ---------------------------------------------------------------------------
# categories/{slug}.json
# ---------------------------------------------------------------------------

def export_categories(conn, output_dir: str) -> None:
    """Per-category page: metadata, test list, per-model history."""
    cat_dir = os.path.join(output_dir, "categories")

    all_runs = conn.execute(
        """SELECT * FROM benchmark_runs
           WHERE status IN ('completed', 'completed_with_errors')
           ORDER BY started_at ASC"""
    ).fetchall()

    for ccfg in config.CATEGORIES:
        cid = ccfg["id"]
        cslug = ccfg["slug"]

        cat_meta = {
            "id": cid,
            "name": ccfg["name"],
            "slug": cslug,
            "description": ccfg["description"],
            "icon": ccfg.get("icon", ""),
            "weight": ccfg["weight"],
        }

        tests_data = [
            {
                "id": _display_test_id(t["id"]),
                "name": t["name"],
                "description": t["description"],
            }
            for t in config.get_tests_for_category(cid)
        ]

        # Per-model current score + history
        models_data = {}
        for mcfg in config.MODELS:
            mid = mcfg["id"]
            mslug = mcfg["slug"]

            # Current (from this model's latest run)
            model_run = _get_latest_run_for_model(conn, mid)
            current_score = None
            if model_run:
                cs = conn.execute(
                    "SELECT avg_score FROM run_scores WHERE run_id = ? AND model_id = ? AND category_id = ?",
                    (model_run["id"], mid, cid),
                ).fetchone()
                if cs:
                    current_score = _round_score(cs["avg_score"])

            # Full history
            history = []
            for run in all_runs:
                run = dict(run)
                rs = conn.execute(
                    "SELECT avg_score FROM run_scores WHERE run_id = ? AND model_id = ? AND category_id = ?",
                    (run["id"], mid, cid),
                ).fetchone()
                if rs:
                    history.append({
                        "timestamp": _iso(run["started_at"]),
                        "score": _round_score(rs["avg_score"]),
                    })

            models_data[mslug] = {
                "currentScore": current_score,
                "history": history,
            }

        _write_json(os.path.join(cat_dir, f"{cslug}.json"), {
            "category": cat_meta,
            "tests": tests_data,
            "models": models_data,
        })


# ---------------------------------------------------------------------------
# trends/*.json
# ---------------------------------------------------------------------------

def export_trends(conn, output_dir: str) -> None:
    """Generate daily, weekly, monthly, yearly composite trend files."""
    trends_dir = os.path.join(output_dir, "trends")
    _export_daily_trends(conn, trends_dir)
    _export_weekly_trends(conn, trends_dir)
    _export_monthly_trends(conn, trends_dir)
    _export_yearly_trends(conn, trends_dir)


def _collect_run_composites(conn, days: int) -> list[tuple[dict, list[dict]]]:
    """Return [(run, [model_run_scores])] for runs in the last *days*."""
    runs = database.get_all_runs(conn, days=days)
    result = []
    for run in runs:
        comps = database.get_model_run_scores_for_run(conn, run["id"])
        result.append((run, comps))
    return result


def _export_daily_trends(conn, trends_dir: str) -> None:
    """Every run in the last 30 days as a data point."""
    pairs = _collect_run_composites(conn, days=30)
    data = []
    for run, comps in pairs:
        models = {}
        for mc in comps:
            models[mc["model_slug"]] = _round_score(mc["composite_score"])
        if models:
            data.append({"timestamp": _iso(run["started_at"]), "models": models})

    _write_json(os.path.join(trends_dir, "daily.json"), {
        "period": "daily",
        "data": data,
    })


def _export_weekly_trends(conn, trends_dir: str) -> None:
    """Averaged per ISO week, last 90 days."""
    pairs = _collect_run_composites(conn, days=90)
    weeks = defaultdict(lambda: defaultdict(list))
    week_starts = {}

    for run, comps in pairs:
        try:
            dt = datetime.fromisoformat(run["started_at"].replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            continue
        monday = dt - timedelta(days=dt.weekday())
        wk = monday.strftime("%Y-%m-%d")
        week_starts[wk] = monday
        for mc in comps:
            weeks[wk][mc["model_slug"]].append(mc["composite_score"])

    data = []
    for wk in sorted(weeks):
        ws = week_starts[wk]
        models = {s: _round_score(sum(v) / len(v)) for s, v in weeks[wk].items()}
        data.append({
            "timestamp": ws.strftime("%Y-%m-%dT00:00:00.000Z"),
            "weekLabel": f"Week of {ws.strftime('%m-%d')}",
            "models": models,
        })

    _write_json(os.path.join(trends_dir, "weekly.json"), {
        "period": "weekly",
        "data": data,
    })


def _export_monthly_trends(conn, trends_dir: str) -> None:
    """Averaged per calendar month, last 180 days."""
    pairs = _collect_run_composites(conn, days=180)
    months = defaultdict(lambda: defaultdict(list))

    for run, comps in pairs:
        try:
            dt = datetime.fromisoformat(run["started_at"].replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            continue
        mk = dt.strftime("%Y-%m")
        for mc in comps:
            months[mk][mc["model_slug"]].append(mc["composite_score"])

    data = []
    for mk in sorted(months):
        models = {s: _round_score(sum(v) / len(v)) for s, v in months[mk].items()}
        data.append({
            "timestamp": f"{mk}-01T00:00:00.000Z",
            "monthLabel": mk,
            "models": models,
        })

    _write_json(os.path.join(trends_dir, "monthly.json"), {
        "period": "monthly",
        "data": data,
    })


def _export_yearly_trends(conn, trends_dir: str) -> None:
    """Monthly averages over the last 365 days."""
    pairs = _collect_run_composites(conn, days=365)
    months = defaultdict(lambda: defaultdict(list))

    for run, comps in pairs:
        try:
            dt = datetime.fromisoformat(run["started_at"].replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            continue
        mk = dt.strftime("%Y-%m")
        for mc in comps:
            months[mk][mc["model_slug"]].append(mc["composite_score"])

    data = []
    for mk in sorted(months):
        models = {s: _round_score(sum(v) / len(v)) for s, v in months[mk].items()}
        data.append({
            "timestamp": f"{mk}-01T00:00:00.000Z",
            "monthLabel": mk,
            "models": models,
        })

    _write_json(os.path.join(trends_dir, "yearly.json"), {
        "period": "yearly",
        "data": data,
    })


# ---------------------------------------------------------------------------
# regressions.json
# ---------------------------------------------------------------------------

def export_regressions(conn, output_dir: str) -> None:
    """Active + recently resolved regressions."""
    active_rows = database.get_active_regressions(conn)
    recent_rows = database.get_recent_regressions(conn, days=30)

    def _fmt(r: dict) -> dict:
        return {
            "id": r["id"],
            "modelId": r["model_slug"],
            "modelName": r["model_name"],
            "categoryId": r.get("category_slug"),
            "categoryName": r.get("category_name"),
            "detectedAt": _iso(r["detected_at"]),
            "previousAvg": _round_score(r["previous_avg"]),
            "currentScore": _round_score(r["current_score"]),
            "dropPct": _round_score(r["drop_pct"]),
            "severity": r["severity"],
            "windowDays": r["window_days"],
            "resolvedAt": _iso(r.get("resolved_at")),
        }

    _write_json(os.path.join(output_dir, "regressions.json"), {
        "active": [_fmt(r) for r in active_rows],
        "recent": [_fmt(r) for r in recent_rows],
    })


# ---------------------------------------------------------------------------
# outages.json
# ---------------------------------------------------------------------------

def export_outages(conn, output_dir: str) -> None:
    """Current + historical outages + per-provider uptime percentages."""
    all_outages = database.get_all_outages(conn, days=90)

    current = []
    history = []
    for o in all_outages:
        entry = {
            "id": o["id"],
            "provider": o["provider"],
            "modelId": o["model_slug"],
            "startedAt": _iso(o["started_at"]),
            "endedAt": _iso(o.get("ended_at")),
            "errorType": o["error_type"],
            "errorMessage": o["error_message"],
            "httpStatus": o["http_status"],
            "checkCount": o["check_count"],
        }
        if o["ended_at"] is None:
            current.append(entry)
        else:
            history.append(entry)

    _write_json(os.path.join(output_dir, "outages.json"), {
        "current": current,
        "history": history,
        "uptime": _compute_uptime(conn),
    })


def _compute_uptime(conn) -> dict:
    """Per-provider uptime for 7d / 30d / 90d windows."""
    providers = {}
    for mcfg in config.MODELS:
        p = mcfg["cli"]
        if p not in providers:
            providers[p] = {}

    now = datetime.now(timezone.utc)
    for provider in providers:
        for label, days in [("7d", 7), ("30d", 30), ("90d", 90)]:
            cutoff = (now - timedelta(days=days)).isoformat()
            total_minutes = days * 24 * 60

            rows = conn.execute(
                """SELECT o.started_at, o.ended_at
                   FROM outages o
                   JOIN models m ON o.model_id = m.id
                   WHERE m.provider = ? AND o.started_at >= ?""",
                (provider, cutoff),
            ).fetchall()

            down_minutes = 0.0
            for row in rows:
                try:
                    start = datetime.fromisoformat(row["started_at"].replace("Z", "+00:00"))
                    end = (
                        datetime.fromisoformat(row["ended_at"].replace("Z", "+00:00"))
                        if row["ended_at"]
                        else now
                    )
                    down_minutes += max(0, (end - start).total_seconds() / 60)
                except (ValueError, TypeError):
                    continue

            pct = round((1 - down_minutes / total_minutes) * 100, 1) if total_minutes > 0 else 100
            pct = max(0.0, pct)
            # 100.0 -> 100,  99.5 stays 99.5
            providers[provider][label] = int(pct) if pct == int(pct) else pct

    return providers


# ---------------------------------------------------------------------------
# evidence/{run-label}/{test-id}.json
# ---------------------------------------------------------------------------

def export_evidence(conn, output_dir: str) -> None:
    """Full test evidence for runs within the last 30 days."""
    evidence_dir = os.path.join(output_dir, "evidence")
    runs = database.get_all_runs(conn, days=30)

    for run in runs:
        run_id = run["id"]
        rlabel = _run_label(run)
        run_dir = os.path.join(evidence_dir, rlabel)

        results = database.get_test_results_for_run(conn, run_id)

        # Group by test
        by_test = defaultdict(dict)
        for r in results:
            dtid = _display_test_id(r["test_id"])
            if dtid not in by_test:
                # Look up the full prompt from the tests table
                test_row = conn.execute(
                    "SELECT prompt FROM tests WHERE id = ?",
                    (r["test_id"],),
                ).fetchone()
                prompt_text = (dict(test_row)["prompt"] if test_row and dict(test_row).get("prompt") else r["test_description"])

                by_test[dtid] = {
                    "test": {
                        "id": dtid,
                        "name": r["test_name"],
                        "category": r["category_slug"],
                        "categoryName": r["category_name"],
                        "description": r["test_description"] or "",
                        "prompt": prompt_text or "",
                    },
                    "results": {},
                }

            eval_details = None
            if r.get("eval_details"):
                try:
                    eval_details = json.loads(r["eval_details"])
                except (json.JSONDecodeError, TypeError):
                    pass

            by_test[dtid]["results"][r["model_slug"]] = {
                "score": _round_score(r["score"]),
                "modelOutput": r.get("model_output") or "",
                "evalDetails": eval_details,
                "latencyMs": r["latency_ms"],
                "tokenCount": r.get("token_count"),
                "error": r.get("error"),
            }

        if by_test:
            os.makedirs(run_dir, exist_ok=True)
            for test_key, data in by_test.items():
                _write_json(os.path.join(run_dir, f"{test_key}.json"), data)


# ---------------------------------------------------------------------------
# Empty stubs (no data yet)
# ---------------------------------------------------------------------------

def _generate_empty_stubs(output_dir: str) -> None:
    """Write minimal valid JSON so the Next.js site still builds."""
    _write_json(os.path.join(output_dir, "latest.json"), {
        "runId": None, "startedAt": None, "completedAt": None,
        "schedule": None, "models": {},
    })
    _write_json(os.path.join(output_dir, "synopsis.json"), {
        "day": {"modelId": None, "name": None, "score": None, "change": 0},
        "week": {"modelId": None, "name": None, "score": None, "change": 0},
        "month": {"modelId": None, "name": None, "score": None, "change": 0},
        "updatedAt": None,
    })
    _write_json(os.path.join(output_dir, "regressions.json"), {
        "active": [], "recent": [],
    })
    _write_json(os.path.join(output_dir, "outages.json"), {
        "current": [], "history": [], "uptime": {},
    })
    for period in ("daily", "weekly", "monthly", "yearly"):
        _write_json(os.path.join(output_dir, "trends", f"{period}.json"), {
            "period": period, "data": [],
        })
    for mcfg in config.MODELS:
        _write_json(os.path.join(output_dir, "models", f"{mcfg['slug']}.json"), {
            "model": {
                "id": mcfg["id"], "provider": mcfg["cli"],
                "name": mcfg["name"], "slug": mcfg["slug"],
                "color": mcfg["color"], "icon": mcfg.get("icon", "cpu"),
            },
            "current": {"compositeScore": None, "rank": None, "categories": {}},
            "history": [], "regressions": [], "outages": [],
        })
    for ccfg in config.CATEGORIES:
        tests_data = [
            {"id": _display_test_id(t["id"]), "name": t["name"], "description": t["description"]}
            for t in config.get_tests_for_category(ccfg["id"])
        ]
        _write_json(os.path.join(output_dir, "categories", f"{ccfg['slug']}.json"), {
            "category": {
                "id": ccfg["id"], "name": ccfg["name"], "slug": ccfg["slug"],
                "description": ccfg["description"],
                "icon": ccfg.get("icon", ""), "weight": ccfg["weight"],
            },
            "tests": tests_data, "models": {},
        })


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def export_all(output_dir: str, db_path: str | None = None) -> None:
    """Export every JSON file the website needs."""
    conn = database.get_connection(db_path)

    # Check for any completed runs
    row = conn.execute(
        "SELECT COUNT(*) as cnt FROM benchmark_runs WHERE status IN ('completed', 'completed_with_errors')"
    ).fetchone()
    has_data = dict(row)["cnt"] > 0

    if not has_data:
        logger.warning("No completed runs in database -- writing empty stubs.")
        _generate_empty_stubs(output_dir)
        conn.close()
        return

    logger.info("Exporting JSON data to %s ...", output_dir)
    os.makedirs(output_dir, exist_ok=True)

    export_latest(conn, output_dir)
    logger.info("  latest.json")

    export_synopsis(conn, output_dir)
    logger.info("  synopsis.json")

    export_models(conn, output_dir)
    logger.info("  models/*.json")

    export_categories(conn, output_dir)
    logger.info("  categories/*.json")

    export_trends(conn, output_dir)
    logger.info("  trends/*.json")

    export_regressions(conn, output_dir)
    logger.info("  regressions.json")

    export_outages(conn, output_dir)
    logger.info("  outages.json")

    export_evidence(conn, output_dir)
    logger.info("  evidence/*.json")

    conn.close()
    logger.info("Export complete.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export benchmark data from SQLite to JSON for the Next.js website",
    )
    parser.add_argument(
        "--output",
        default=os.path.join(_SCRIPT_DIR, "..", "public", "data"),
        help="Output directory for JSON files (default: ../public/data)",
    )
    parser.add_argument(
        "--db",
        default=os.path.join(_SCRIPT_DIR, "data", "benchmarks.db"),
        help="Path to SQLite database (default: data/benchmarks.db)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable debug logging",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    export_all(args.output, args.db)


if __name__ == "__main__":
    main()
