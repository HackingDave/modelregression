"""
Score aggregation for benchmark runs.

Computes per-category averages and weighted composite scores.
"""

import logging

import config
import db as database

logger = logging.getLogger(__name__)


def aggregate_run_scores(conn, run_id: str) -> None:
    """
    Compute avg/min/max scores per model per category for a run.

    Reads from test_results and writes to run_scores.
    """
    rows = conn.execute(
        """SELECT model_id, category_id,
                  AVG(score) as avg_score,
                  MIN(score) as min_score,
                  MAX(score) as max_score,
                  COUNT(*) as test_count
           FROM test_results
           WHERE run_id = ? AND score IS NOT NULL
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

    logger.info("Aggregated %d model-category score entries for run %s", len(rows), run_id)


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

    # Compute weighted average for each model
    composites: list[tuple[str, float]] = []
    for model_id, cat_scores in model_scores.items():
        weighted_sum = 0.0
        actual_weight = 0.0
        for cat_id, score in cat_scores.items():
            w = weight_map.get(cat_id, 0)
            weighted_sum += score * w
            actual_weight += w

        if actual_weight > 0:
            composite = round(weighted_sum / actual_weight, 1)
        else:
            composite = 0.0

        composites.append((model_id, composite))

    # Sort by composite descending to assign ranks
    composites.sort(key=lambda x: x[1], reverse=True)

    for rank, (model_id, composite) in enumerate(composites, start=1):
        database.save_model_run_score(conn, run_id, model_id, composite, rank)
        logger.info("  %s: composite=%.1f rank=%d", model_id, composite, rank)

    logger.info("Computed composite scores for %d models in run %s", len(composites), run_id)
