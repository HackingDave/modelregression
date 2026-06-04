"""
Regression detection for benchmark runs.

After each run, compares current scores against recent history
to detect significant drops.
"""

import logging

import config
import db as database

logger = logging.getLogger(__name__)

# Severity thresholds (percentage drop)
MINOR_THRESHOLD = 3.0
MODERATE_THRESHOLD = 5.0
MAJOR_THRESHOLD = 15.0

# Recovery: must be within this percentage of pre-regression avg
# for CONSECUTIVE_RECOVERY_RUNS consecutive runs
RECOVERY_TOLERANCE = 2.0
CONSECUTIVE_RECOVERY_RUNS = 3

WINDOW_DAYS = 7


def _classify_severity(drop_pct: float) -> str | None:
    """Classify regression severity based on percentage drop."""
    abs_drop = abs(drop_pct)
    if abs_drop >= MAJOR_THRESHOLD:
        return "major"
    elif abs_drop >= MODERATE_THRESHOLD:
        return "moderate"
    elif abs_drop >= MINOR_THRESHOLD:
        return "minor"
    return None


def detect_regressions(conn, run_id: str) -> None:
    """
    Compare current run scores against 7-day averages.
    Create regression records for significant drops.
    Also check if existing regressions have recovered.
    """
    logger.info("Running regression detection for run %s", run_id)

    # Get current run's scores
    run_scores = database.get_run_scores_for_run(conn, run_id)
    model_composites = database.get_model_run_scores_for_run(conn, run_id)

    # --- Category-level regression detection ---
    for rs in run_scores:
        model_id = rs["model_id"]
        category_id = rs["category_id"]
        current_score = rs["avg_score"]

        if current_score is None:
            continue

        # Get historical average
        history = database.get_historical_category_scores(
            conn, model_id, category_id, days=WINDOW_DAYS
        )
        # Exclude the current run from the average
        past_scores = [h["avg_score"] for h in history if h["run_id"] != run_id and h["avg_score"] is not None]

        if len(past_scores) < 3:
            # Not enough history to detect regression
            continue

        avg_score = sum(past_scores) / len(past_scores)
        if avg_score == 0:
            continue

        drop_pct = ((current_score - avg_score) / avg_score) * 100
        severity = _classify_severity(drop_pct)

        if severity and drop_pct < 0:
            # Check if we already have an active regression for this model+category
            existing = conn.execute(
                """SELECT id FROM regressions
                   WHERE model_id = ? AND category_id = ? AND resolved_at IS NULL""",
                (model_id, category_id),
            ).fetchone()

            if not existing:
                database.create_regression(
                    conn,
                    model_id=model_id,
                    category_id=category_id,
                    run_id=run_id,
                    previous_avg=round(avg_score, 1),
                    current_score=round(current_score, 1),
                    drop_pct=round(drop_pct, 1),
                    severity=severity,
                    window_days=WINDOW_DAYS,
                )

    # --- Composite-level regression detection ---
    for mc in model_composites:
        model_id = mc["model_id"]
        current_composite = mc["composite_score"]

        if current_composite is None:
            continue

        history = database.get_historical_scores(conn, model_id, days=WINDOW_DAYS)
        past_composites = [h["composite_score"] for h in history if h["run_id"] != run_id and h["composite_score"] is not None]

        if len(past_composites) < 3:
            continue

        avg_composite = sum(past_composites) / len(past_composites)
        if avg_composite == 0:
            continue

        drop_pct = ((current_composite - avg_composite) / avg_composite) * 100
        severity = _classify_severity(drop_pct)

        if severity and drop_pct < 0:
            existing = conn.execute(
                """SELECT id FROM regressions
                   WHERE model_id = ? AND category_id IS NULL AND resolved_at IS NULL""",
                (model_id,),
            ).fetchone()

            if not existing:
                database.create_regression(
                    conn,
                    model_id=model_id,
                    category_id=None,
                    run_id=run_id,
                    previous_avg=round(avg_composite, 1),
                    current_score=round(current_composite, 1),
                    drop_pct=round(drop_pct, 1),
                    severity=severity,
                    window_days=WINDOW_DAYS,
                    notes="Composite score regression",
                )

    # --- Check for recovery of existing regressions ---
    _check_recovery(conn, run_id)


def _check_recovery(conn, run_id: str) -> None:
    """Check if any active regressions have recovered."""
    active_regs = database.get_active_regressions(conn)

    for reg in active_regs:
        model_id = reg["model_id"]
        category_id = reg["category_id"]
        previous_avg = reg["previous_avg"]

        if previous_avg is None:
            continue

        if category_id:
            # Category-level recovery check
            history = database.get_historical_category_scores(
                conn, model_id, category_id, days=WINDOW_DAYS
            )
        else:
            # Composite-level recovery check
            history = database.get_historical_scores(conn, model_id, days=WINDOW_DAYS)

        if len(history) < CONSECUTIVE_RECOVERY_RUNS:
            continue

        # Check the most recent N runs
        recent = history[-CONSECUTIVE_RECOVERY_RUNS:]
        score_key = "avg_score" if category_id else "composite_score"

        all_recovered = all(
            h[score_key] is not None and
            abs(h[score_key] - previous_avg) / previous_avg * 100 <= RECOVERY_TOLERANCE
            for h in recent
        )

        if all_recovered:
            database.resolve_regression(
                conn,
                reg["id"],
                notes=f"Recovered: last {CONSECUTIVE_RECOVERY_RUNS} runs within {RECOVERY_TOLERANCE}% of pre-regression avg",
            )
            logger.info(
                "Regression %s resolved (model=%s, category=%s)",
                reg["id"], model_id, category_id,
            )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Standalone: detect regressions for the latest run
    conn = database.init_db()
    latest = database.get_latest_run(conn)
    if latest:
        detect_regressions(conn, latest["id"])
    else:
        print("No completed runs found.")
    conn.close()
