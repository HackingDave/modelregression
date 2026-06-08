from pathlib import Path
import sys

BENCHMARK_DIR = Path(__file__).resolve().parent
if str(BENCHMARK_DIR) not in sys.path:
    sys.path.insert(0, str(BENCHMARK_DIR))

import db
import scoring


def _save_result(
    conn,
    run_id: str,
    model_id: str,
    test_id: str,
    category_id: str,
    score: float | None,
    tokens: int | None = 100,
    error: str | None = None,
) -> None:
    db.save_test_result(
        conn,
        run_id,
        model_id,
        test_id,
        category_id,
        score=score,
        raw_score=score,
        latency_ms=1000,
        token_count=tokens,
        prompt_tokens=(tokens // 2) if tokens is not None else None,
        completion_tokens=(tokens - (tokens // 2)) if tokens is not None else None,
        model_output="ok" if error is None else None,
        eval_details={"grade": "A"} if error is None else None,
        error=error,
    )


def test_aggregate_run_scores_adds_token_efficiency_category(tmp_path):
    conn = db.init_db(str(tmp_path / "benchmarks.db"))
    db.seed_models_and_categories(conn)

    run_id = db.create_run(conn, "daily")

    def save(model_id: str, test_id: str, category_id: str, score: float, tokens: int):
        _save_result(
            conn,
            run_id,
            model_id,
            test_id,
            category_id,
            score,
            tokens,
        )

    save("claude-opus-4-8", "bf-1", "bug-fixes", 95, 100)
    save("claude-opus-4-8", "bf-2", "bug-fixes", 90, 200)
    save("gpt-5-5", "bf-1", "bug-fixes", 95, 300)
    save("gpt-5-5", "bf-2", "bug-fixes", 90, 300)

    scoring.aggregate_run_scores(conn, run_id)

    rows = conn.execute(
        """SELECT model_id, avg_score, test_count
           FROM run_scores
           WHERE run_id = ? AND category_id = 'token-efficiency'
           ORDER BY model_id""",
        (run_id,),
    ).fetchall()

    assert [dict(row) for row in rows] == [
        {"model_id": "claude-opus-4-8", "avg_score": 100.0, "test_count": 2},
        {"model_id": "gpt-5-5", "avg_score": 50.0, "test_count": 2},
    ]


def test_aggregate_run_scores_counts_null_scores_as_zero(tmp_path):
    conn = db.init_db(str(tmp_path / "benchmarks.db"))
    db.seed_models_and_categories(conn)
    run_id = db.create_run(conn, "daily")

    _save_result(conn, run_id, "gpt-5-5", "bf-1", "bug-fixes", 100)
    _save_result(
        conn,
        run_id,
        "gpt-5-5",
        "bf-2",
        "bug-fixes",
        None,
        tokens=None,
        error="CLI call timed out",
    )
    _save_result(conn, run_id, "gpt-5-5", "bf-3", "bug-fixes", 0)

    scoring.aggregate_run_scores(conn, run_id)

    row = conn.execute(
        """SELECT avg_score, min_score, max_score, test_count
           FROM run_scores
           WHERE run_id = ? AND model_id = ? AND category_id = ?""",
        (run_id, "gpt-5-5", "bug-fixes"),
    ).fetchone()

    assert dict(row) == {
        "avg_score": 33.3,
        "min_score": 0.0,
        "max_score": 100.0,
        "test_count": 3,
    }


def test_compute_composite_scores_counts_missing_category_as_zero(tmp_path):
    conn = db.init_db(str(tmp_path / "benchmarks.db"))
    db.seed_models_and_categories(conn)
    run_id = db.create_run(conn, "daily")

    db.save_run_scores(conn, run_id, "claude-opus-4-8", "bug-fixes", 100, 100, 100, 1)
    db.save_run_scores(conn, run_id, "claude-opus-4-8", "security-awareness", 100, 100, 100, 1)
    db.save_run_scores(conn, run_id, "gpt-5-5", "bug-fixes", 100, 100, 100, 1)

    scoring.compute_composite_scores(conn, run_id)

    rows = conn.execute(
        """SELECT model_id, composite_score, rank
           FROM model_run_scores
           WHERE run_id = ?
           ORDER BY rank""",
        (run_id,),
    ).fetchall()

    assert [dict(row) for row in rows] == [
        {"model_id": "claude-opus-4-8", "composite_score": 100.0, "rank": 1},
        {"model_id": "gpt-5-5", "composite_score": 50.0, "rank": 2},
    ]
