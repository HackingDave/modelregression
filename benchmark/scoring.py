"""
Score aggregation for benchmark runs.

Computes per-category averages and weighted composite scores.
"""

import logging

import config
import db as database

logger = logging.getLogger(__name__)
TOKEN_EFFICIENCY_CATEGORY_ID = "token-efficiency"


def aggregate_run_scores(conn, run_id: str) -> None:
    """
    Compute avg/min/max scores per model per category for a run.

    Reads from test_results and writes to run_scores.
    """
    rows = conn.execute(
        """SELECT model_id, category_id,
                  AVG(COALESCE(score, 0)) as avg_score,
                  MIN(COALESCE(score, 0)) as min_score,
                  MAX(COALESCE(score, 0)) as max_score,
                  COUNT(*) as test_count
           FROM test_results
           WHERE run_id = ?
           GROUP BY model_id, category_id""",
        (run_id,),
    ).fetchall()

    for row in rows:
        database.save_run_scores(
            conn,
            run_id=run_id,
            model_id=row["model_id"],
            category_id=row["category_id"],
            avg_score=round(row["avg_score"], 1),
            min_score=round(row["min_score"], 1),
            max_score=round(row["max_score"], 1),
            test_count=row["test_count"],
        )

    _save_token_efficiency_scores(conn, run_id)

    logger.info("Aggregated %d model-category score entries for run %s", len(rows), run_id)


def _save_token_efficiency_scores(conn, run_id: str) -> None:
    """Create a synthetic category score based on average tokens per successful test."""
    rows = conn.execute(
        """SELECT model_id,
                  SUM(token_count) as total_tokens,
                  COUNT(*) as successful_tests
           FROM test_results
           WHERE run_id = ? AND score IS NOT NULL AND token_count > 0
           GROUP BY model_id""",
        (run_id,),
    ).fetchall()

    if not rows:
        logger.info("No token-usage rows available for synthetic scoring in run %s", run_id)
        return

    averages = {
        row["model_id"]: row["total_tokens"] / row["successful_tests"]
        for row in rows
        if row["total_tokens"] and row["successful_tests"]
    }
    if not averages:
        return

    best_avg_tokens = min(averages.values())

    for row in rows:
        avg_tokens = averages.get(row["model_id"])
        if not avg_tokens or avg_tokens <= 0:
            continue

        # Lowest average token burn gets 100. Higher usage is penalized proportionally.
        efficiency_score = round(min(100.0, (best_avg_tokens / avg_tokens) * 100), 1)
        database.save_run_scores(
            conn,
            run_id=run_id,
            model_id=row["model_id"],
            category_id=TOKEN_EFFICIENCY_CATEGORY_ID,
            avg_score=efficiency_score,
            min_score=efficiency_score,
            max_score=efficiency_score,
            test_count=row["successful_tests"],
        )


def compute_composite_scores(conn, run_id: str) -> None:
    """
    Compute weighted composite scores for each model using category weights.

    Reads from run_scores and category weights, writes to model_run_scores.
    """
    # Build weight map
    weight_map = {}
    total_weight = 0.0
    for cat in config.CATEGORIES:
        weight_map[cat["id"]] = cat["weight"]
        total_weight += cat["weight"]

    if total_weight == 0:
        logger.error("Total category weight is zero, cannot compute composites")
        return

    # Get all run_scores for this run, grouped by model
    rows = conn.execute(
        """SELECT model_id, category_id, avg_score
           FROM run_scores
           WHERE run_id = ?""",
        (run_id,),
    ).fetchall()

    # Group by model
    model_scores: dict[str, dict[str, float]] = {}
    for row in rows:
        model_id = row["model_id"]
        if model_id not in model_scores:
            model_scores[model_id] = {}
        model_scores[model_id][row["category_id"]] = row["avg_score"]

    categories_in_run = {row["category_id"] for row in rows}
    weighted_categories = [
        (cat["id"], cat["weight"])
        for cat in config.CATEGORIES
        if cat["id"] in categories_in_run and cat["weight"] > 0
    ]
    if not weighted_categories:
        logger.warning("No weighted category scores available for run %s", run_id)
        return

    # Compute weighted average for each model. Missing category rows count as 0
    # if that category was scored by any model in the same run.
    composites: list[tuple[str, float]] = []
    for model_id, cat_scores in model_scores.items():
        weighted_sum = 0.0
        actual_weight = 0.0
        for cat_id, w in weighted_categories:
            raw_score = cat_scores.get(cat_id)
            score = float(raw_score) if raw_score is not None else 0.0
            weighted_sum += score * w
            actual_weight += w

        composite = round(weighted_sum / actual_weight, 1)

        composites.append((model_id, composite))

    # Sort by composite descending to assign ranks
    composites.sort(key=lambda x: x[1], reverse=True)

    for rank, (model_id, composite) in enumerate(composites, start=1):
        database.save_model_run_score(conn, run_id, model_id, composite, rank)
        logger.info("  %s: composite=%.1f rank=%d", model_id, composite, rank)

    logger.info("Computed composite scores for %d models in run %s", len(composites), run_id)
