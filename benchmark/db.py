"""
SQLite database manager for ModelRegression benchmark engine.
"""

import json
import logging
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any

from config import CATEGORIES, DB_PATH, MODELS, TESTS
from tests import ALL_TESTS

_TEST_PROMPTS = {t.id: t.prompt for t in ALL_TESTS}

logger = logging.getLogger(__name__)


def _generate_id() -> str:
    return str(uuid.uuid4())


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_connection(db_path: str | None = None) -> sqlite3.Connection:
    """Return a connection to the benchmark database."""
    path = db_path or DB_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# ---- Schema ----------------------------------------------------------------

_SCHEMA = """
CREATE TABLE IF NOT EXISTS models (
    id TEXT PRIMARY KEY,
    provider TEXT NOT NULL,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    cli_model TEXT NOT NULL,
    color TEXT NOT NULL,
    icon TEXT NOT NULL DEFAULT 'cpu',
    is_active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS categories (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    description TEXT,
    weight REAL NOT NULL DEFAULT 1.0,
    sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS tests (
    id TEXT PRIMARY KEY,
    category_id TEXT NOT NULL REFERENCES categories(id),
    name TEXT NOT NULL,
    description TEXT,
    prompt TEXT,
    eval_type TEXT NOT NULL DEFAULT 'llm_judge',
    eval_config TEXT,
    max_score REAL NOT NULL DEFAULT 100.0,
    is_active INTEGER NOT NULL DEFAULT 1,
    version INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS benchmark_runs (
    id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    schedule TEXT,
    status TEXT NOT NULL DEFAULT 'running',
    total_tests INTEGER NOT NULL DEFAULT 0,
    passed_tests INTEGER NOT NULL DEFAULT 0,
    error_log TEXT
);

CREATE TABLE IF NOT EXISTS run_models (
    run_id TEXT NOT NULL REFERENCES benchmark_runs(id),
    model_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    name TEXT NOT NULL,
    slug TEXT NOT NULL,
    cli_model TEXT NOT NULL,
    color TEXT NOT NULL,
    icon TEXT NOT NULL DEFAULT 'cpu',
    config_json TEXT,
    PRIMARY KEY (run_id, model_id)
);

CREATE TABLE IF NOT EXISTS test_results (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES benchmark_runs(id),
    model_id TEXT NOT NULL REFERENCES models(id),
    test_id TEXT NOT NULL REFERENCES tests(id),
    category_id TEXT NOT NULL REFERENCES categories(id),
    score REAL,
    raw_score REAL,
    latency_ms INTEGER,
    token_count INTEGER,
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    model_output TEXT,
    eval_details TEXT,
    error TEXT
);

CREATE TABLE IF NOT EXISTS run_scores (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES benchmark_runs(id),
    model_id TEXT NOT NULL REFERENCES models(id),
    category_id TEXT NOT NULL REFERENCES categories(id),
    avg_score REAL,
    min_score REAL,
    max_score REAL,
    test_count INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS model_run_scores (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES benchmark_runs(id),
    model_id TEXT NOT NULL REFERENCES models(id),
    composite_score REAL,
    rank INTEGER
);

CREATE TABLE IF NOT EXISTS regressions (
    id TEXT PRIMARY KEY,
    model_id TEXT NOT NULL REFERENCES models(id),
    category_id TEXT,
    detected_at TEXT NOT NULL,
    run_id TEXT REFERENCES benchmark_runs(id),
    previous_avg REAL,
    current_score REAL,
    drop_pct REAL,
    severity TEXT,
    window_days INTEGER NOT NULL DEFAULT 7,
    resolved_at TEXT,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS outages (
    id TEXT PRIMARY KEY,
    provider TEXT NOT NULL,
    model_id TEXT NOT NULL REFERENCES models(id),
    started_at TEXT NOT NULL,
    ended_at TEXT,
    error_type TEXT,
    error_message TEXT,
    http_status INTEGER,
    check_count INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_test_results_run ON test_results(run_id);
CREATE INDEX IF NOT EXISTS idx_test_results_model ON test_results(model_id);
CREATE INDEX IF NOT EXISTS idx_run_scores_run ON run_scores(run_id);
CREATE INDEX IF NOT EXISTS idx_model_run_scores_run ON model_run_scores(run_id);
CREATE INDEX IF NOT EXISTS idx_run_models_run ON run_models(run_id);
CREATE INDEX IF NOT EXISTS idx_regressions_model ON regressions(model_id);
CREATE INDEX IF NOT EXISTS idx_outages_model ON outages(model_id);
CREATE INDEX IF NOT EXISTS idx_benchmark_runs_started ON benchmark_runs(started_at);
"""


def init_db(db_path: str | None = None) -> sqlite3.Connection:
    """Create all tables and return the connection."""
    conn = get_connection(db_path)
    conn.executescript(_SCHEMA)
    _ensure_column(conn, "models", "icon", "TEXT NOT NULL DEFAULT 'cpu'")
    conn.commit()
    logger.info("Database initialized at %s", db_path or DB_PATH)
    return conn


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, ddl: str) -> None:
    existing = {
        row["name"]
        for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
    }
    if column not in existing:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")


# ---- Seeding ---------------------------------------------------------------

def seed_models_and_categories(conn: sqlite3.Connection) -> None:
    """Insert or update model and category metadata from config."""
    current_ids = [m["id"] for m in MODELS]
    if current_ids:
        placeholders = ",".join("?" for _ in current_ids)
        conn.execute(
            f"UPDATE models SET is_active = 0 WHERE id NOT IN ({placeholders})",
            current_ids,
        )
    for m in MODELS:
        conn.execute(
            """INSERT OR REPLACE INTO models (id, provider, name, slug, cli_model, color, icon, is_active)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                m["id"], m["cli"], m["name"], m["slug"], m["cli_model"],
                m["color"], m.get("icon", "cpu"), int(m["is_active"]),
            ),
        )
    for c in CATEGORIES:
        conn.execute(
            """INSERT OR REPLACE INTO categories (id, name, slug, description, weight, sort_order)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (c["id"], c["name"], c["slug"], c["description"], c["weight"], c["sort_order"]),
        )
    for t in TESTS:
        prompt = _TEST_PROMPTS.get(t["id"], "")
        conn.execute(
            """INSERT OR REPLACE INTO tests (id, category_id, name, description, prompt, eval_type, max_score, version)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (t["id"], t["category_id"], t["name"], t["description"], prompt, t["eval_type"], t["max_score"], t["version"]),
        )
    conn.commit()
    logger.info("Seeded %d models, %d categories, %d tests", len(MODELS), len(CATEGORIES), len(TESTS))


# ---- Benchmark runs --------------------------------------------------------

def create_run(conn: sqlite3.Connection, schedule: str) -> str:
    """Create a new benchmark run record and return its ID."""
    run_id = _generate_id()
    conn.execute(
        """INSERT INTO benchmark_runs (id, started_at, schedule, status)
           VALUES (?, ?, ?, 'running')""",
        (run_id, _now_iso(), schedule),
    )
    conn.commit()
    return run_id


def save_run_model_manifest(conn: sqlite3.Connection, run_id: str, models: list[dict]) -> None:
    """Persist the exact model set selected for a benchmark run."""
    for m in models:
        conn.execute(
            """INSERT OR REPLACE INTO run_models
               (run_id, model_id, provider, name, slug, cli_model, color, icon, config_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                run_id,
                m["id"],
                m["cli"],
                m["name"],
                m["slug"],
                m["cli_model"],
                m["color"],
                m.get("icon", "cpu"),
                json.dumps(m, default=str),
            ),
        )
    conn.commit()


def get_run_model_manifest(conn: sqlite3.Connection, run_id: str) -> list[dict]:
    """Return model metadata saved for a benchmark run."""
    rows = conn.execute(
        """SELECT model_id as id, provider, name, slug, cli_model, color, icon, config_json
           FROM run_models
           WHERE run_id = ?
           ORDER BY name""",
        (run_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def complete_run(conn: sqlite3.Connection, run_id: str, total_tests: int, passed_tests: int, error_log: str | None = None) -> None:
    """Mark a run as completed."""
    status = "completed" if error_log is None else "completed_with_errors"
    conn.execute(
        """UPDATE benchmark_runs
           SET completed_at = ?, status = ?, total_tests = ?, passed_tests = ?, error_log = ?
           WHERE id = ?""",
        (_now_iso(), status, total_tests, passed_tests, error_log, run_id),
    )
    conn.commit()


def fail_run(conn: sqlite3.Connection, run_id: str, error_log: str) -> None:
    """Mark a run as failed."""
    conn.execute(
        """UPDATE benchmark_runs SET completed_at = ?, status = 'failed', error_log = ? WHERE id = ?""",
        (_now_iso(), error_log, run_id),
    )
    conn.commit()


# ---- Test results ----------------------------------------------------------

def save_test_result(
    conn: sqlite3.Connection,
    run_id: str,
    model_id: str,
    test_id: str,
    category_id: str,
    score: float | None,
    raw_score: float | None,
    latency_ms: int | None,
    token_count: int | None,
    prompt_tokens: int | None,
    completion_tokens: int | None,
    model_output: str | None,
    eval_details: dict | None,
    error: str | None,
) -> str:
    """Save a single test result and return its ID."""
    result_id = _generate_id()
    conn.execute(
        """INSERT INTO test_results
           (id, run_id, model_id, test_id, category_id, score, raw_score,
            latency_ms, token_count, prompt_tokens, completion_tokens,
            model_output, eval_details, error)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            result_id, run_id, model_id, test_id, category_id,
            score, raw_score, latency_ms, token_count,
            prompt_tokens, completion_tokens, model_output,
            json.dumps(eval_details) if eval_details else None,
            error,
        ),
    )
    conn.commit()
    return result_id


# ---- Run scores ------------------------------------------------------------

def save_run_scores(
    conn: sqlite3.Connection,
    run_id: str,
    model_id: str,
    category_id: str,
    avg_score: float,
    min_score: float,
    max_score: float,
    test_count: int,
) -> str:
    """Save aggregated run scores for a model+category."""
    score_id = _generate_id()
    conn.execute(
        """INSERT INTO run_scores (id, run_id, model_id, category_id, avg_score, min_score, max_score, test_count)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (score_id, run_id, model_id, category_id, avg_score, min_score, max_score, test_count),
    )
    conn.commit()
    return score_id


def save_model_run_score(
    conn: sqlite3.Connection,
    run_id: str,
    model_id: str,
    composite_score: float,
    rank: int,
) -> str:
    """Save the composite score and rank for a model in a run."""
    score_id = _generate_id()
    conn.execute(
        """INSERT INTO model_run_scores (id, run_id, model_id, composite_score, rank)
           VALUES (?, ?, ?, ?, ?)""",
        (score_id, run_id, model_id, composite_score, rank),
    )
    conn.commit()
    return score_id


# ---- Historical queries ----------------------------------------------------

def get_historical_scores(conn: sqlite3.Connection, model_id: str, days: int = 7) -> list[dict]:
    """Get composite scores for a model over the past N days."""
    rows = conn.execute(
        """SELECT mrs.composite_score, mrs.rank, br.started_at, br.id as run_id
           FROM model_run_scores mrs
           JOIN benchmark_runs br ON mrs.run_id = br.id
           WHERE mrs.model_id = ?
             AND br.started_at >= datetime('now', ?)
             AND br.status IN ('completed', 'completed_with_errors')
           ORDER BY br.started_at ASC""",
        (model_id, f"-{days} days"),
    ).fetchall()
    return [dict(r) for r in rows]


def get_historical_category_scores(conn: sqlite3.Connection, model_id: str, category_id: str, days: int = 7) -> list[dict]:
    """Get category-level avg scores for a model over the past N days."""
    rows = conn.execute(
        """SELECT rs.avg_score, br.started_at, br.id as run_id
           FROM run_scores rs
           JOIN benchmark_runs br ON rs.run_id = br.id
           WHERE rs.model_id = ?
             AND rs.category_id = ?
             AND br.started_at >= datetime('now', ?)
             AND br.status IN ('completed', 'completed_with_errors')
           ORDER BY br.started_at ASC""",
        (model_id, category_id, f"-{days} days"),
    ).fetchall()
    return [dict(r) for r in rows]


def get_latest_run(conn: sqlite3.Connection) -> dict | None:
    """Get the most recent completed run."""
    row = conn.execute(
        """SELECT * FROM benchmark_runs
           WHERE status IN ('completed', 'completed_with_errors')
           ORDER BY started_at DESC LIMIT 1"""
    ).fetchone()
    return dict(row) if row else None


def get_all_runs(conn: sqlite3.Connection, days: int = 30) -> list[dict]:
    """Get all completed runs in the last N days."""
    rows = conn.execute(
        """SELECT * FROM benchmark_runs
           WHERE status IN ('completed', 'completed_with_errors')
             AND started_at >= datetime('now', ?)
           ORDER BY started_at ASC""",
        (f"-{days} days",),
    ).fetchall()
    return [dict(r) for r in rows]


def get_test_results_for_run(conn: sqlite3.Connection, run_id: str) -> list[dict]:
    """Get all test results for a specific run."""
    rows = conn.execute(
        """SELECT tr.*, t.name as test_name, t.description as test_description,
                  m.name as model_name, m.slug as model_slug,
                  c.name as category_name, c.slug as category_slug
           FROM test_results tr
           JOIN tests t ON tr.test_id = t.id
           JOIN models m ON tr.model_id = m.id
           JOIN categories c ON tr.category_id = c.id
           WHERE tr.run_id = ?
           ORDER BY c.sort_order, t.id, m.name""",
        (run_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def get_run_scores_for_run(conn: sqlite3.Connection, run_id: str) -> list[dict]:
    """Get all run_scores for a specific run."""
    rows = conn.execute(
        """SELECT rs.*, m.slug as model_slug, c.slug as category_slug
           FROM run_scores rs
           JOIN models m ON rs.model_id = m.id
           JOIN categories c ON rs.category_id = c.id
           WHERE rs.run_id = ?""",
        (run_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def get_model_run_scores_for_run(conn: sqlite3.Connection, run_id: str) -> list[dict]:
    """Get all model_run_scores for a specific run."""
    rows = conn.execute(
        """SELECT mrs.*, m.slug as model_slug, m.name as model_name
           FROM model_run_scores mrs
           JOIN models m ON mrs.model_id = m.id
           WHERE mrs.run_id = ?
           ORDER BY mrs.rank ASC""",
        (run_id,),
    ).fetchall()
    return [dict(r) for r in rows]


# ---- Regressions -----------------------------------------------------------

def create_regression(
    conn: sqlite3.Connection,
    model_id: str,
    category_id: str | None,
    run_id: str,
    previous_avg: float,
    current_score: float,
    drop_pct: float,
    severity: str,
    window_days: int = 7,
    notes: str | None = None,
) -> str:
    """Create a new regression record."""
    reg_id = _generate_id()
    conn.execute(
        """INSERT INTO regressions
           (id, model_id, category_id, detected_at, run_id,
            previous_avg, current_score, drop_pct, severity, window_days, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (reg_id, model_id, category_id, _now_iso(), run_id,
         previous_avg, current_score, drop_pct, severity, window_days, notes),
    )
    conn.commit()
    logger.warning("Regression detected: model=%s cat=%s drop=%.1f%% severity=%s",
                    model_id, category_id, drop_pct, severity)
    return reg_id


def resolve_regression(conn: sqlite3.Connection, regression_id: str, notes: str | None = None) -> None:
    """Mark a regression as resolved."""
    conn.execute(
        """UPDATE regressions SET resolved_at = ?, notes = COALESCE(?, notes) WHERE id = ?""",
        (_now_iso(), notes, regression_id),
    )
    conn.commit()
    logger.info("Regression resolved: %s", regression_id)


def get_active_regressions(conn: sqlite3.Connection) -> list[dict]:
    """Get all unresolved regressions."""
    rows = conn.execute(
        """SELECT r.*, m.name as model_name, m.slug as model_slug,
                  c.name as category_name, c.slug as category_slug
           FROM regressions r
           JOIN models m ON r.model_id = m.id
           LEFT JOIN categories c ON r.category_id = c.id
           WHERE r.resolved_at IS NULL
           ORDER BY r.detected_at DESC"""
    ).fetchall()
    return [dict(r) for r in rows]


def get_recent_regressions(conn: sqlite3.Connection, days: int = 30) -> list[dict]:
    """Get recently resolved regressions."""
    rows = conn.execute(
        """SELECT r.*, m.name as model_name, m.slug as model_slug,
                  c.name as category_name, c.slug as category_slug
           FROM regressions r
           JOIN models m ON r.model_id = m.id
           LEFT JOIN categories c ON r.category_id = c.id
           WHERE r.resolved_at IS NOT NULL
             AND r.detected_at >= datetime('now', ?)
           ORDER BY r.detected_at DESC""",
        (f"-{days} days",),
    ).fetchall()
    return [dict(r) for r in rows]


# ---- Outages ---------------------------------------------------------------

def create_or_update_outage(
    conn: sqlite3.Connection,
    provider: str,
    model_id: str,
    error_type: str,
    error_message: str,
    http_status: int | None = None,
) -> str:
    """Create or update an outage record. Returns outage ID."""
    # Check for existing open outage
    row = conn.execute(
        """SELECT id, check_count FROM outages
           WHERE model_id = ? AND ended_at IS NULL
           ORDER BY started_at DESC LIMIT 1""",
        (model_id,),
    ).fetchone()

    if row:
        outage_id = row["id"]
        conn.execute(
            """UPDATE outages
               SET check_count = check_count + 1,
                   error_type = ?, error_message = ?, http_status = ?
               WHERE id = ?""",
            (error_type, error_message, http_status, outage_id),
        )
        conn.commit()
        return outage_id
    else:
        outage_id = _generate_id()
        conn.execute(
            """INSERT INTO outages (id, provider, model_id, started_at, error_type, error_message, http_status, check_count)
               VALUES (?, ?, ?, ?, ?, ?, ?, 1)""",
            (outage_id, provider, model_id, _now_iso(), error_type, error_message, http_status),
        )
        conn.commit()
        return outage_id


def resolve_outage(conn: sqlite3.Connection, model_id: str) -> None:
    """Resolve any open outage for a model."""
    conn.execute(
        """UPDATE outages SET ended_at = ? WHERE model_id = ? AND ended_at IS NULL""",
        (_now_iso(), model_id),
    )
    conn.commit()


def get_open_outage(conn: sqlite3.Connection, model_id: str) -> dict | None:
    """Get the currently open outage for a model, if any."""
    row = conn.execute(
        """SELECT * FROM outages WHERE model_id = ? AND ended_at IS NULL ORDER BY started_at DESC LIMIT 1""",
        (model_id,),
    ).fetchone()
    return dict(row) if row else None


def get_all_outages(conn: sqlite3.Connection, days: int = 90) -> list[dict]:
    """Get all outages in the last N days."""
    rows = conn.execute(
        """SELECT o.*, m.name as model_name, m.slug as model_slug
           FROM outages o
           JOIN models m ON o.model_id = m.id
           WHERE o.started_at >= datetime('now', ?)
           ORDER BY o.started_at DESC""",
        (f"-{days} days",),
    ).fetchall()
    return [dict(r) for r in rows]


def get_active_models(conn: sqlite3.Connection) -> list[dict]:
    """Get all active models."""
    rows = conn.execute("SELECT * FROM models WHERE is_active = 1").fetchall()
    return [dict(r) for r in rows]


def get_active_tests(conn: sqlite3.Connection) -> list[dict]:
    """Get all active tests."""
    rows = conn.execute(
        """SELECT t.*, c.slug as category_slug, c.name as category_name
           FROM tests t
           JOIN categories c ON t.category_id = c.id
           WHERE t.is_active = 1
           ORDER BY c.sort_order, t.id"""
    ).fetchall()
    return [dict(r) for r in rows]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    conn = init_db()
    seed_models_and_categories(conn)
    print("Database initialized and seeded successfully.")
    conn.close()
