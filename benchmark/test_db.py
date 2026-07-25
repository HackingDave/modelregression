from pathlib import Path
import sys

BENCHMARK_DIR = Path(__file__).resolve().parent
if str(BENCHMARK_DIR) not in sys.path:
    sys.path.insert(0, str(BENCHMARK_DIR))

import config
import db


def test_seed_retires_models_that_are_no_longer_in_runtime_catalog(tmp_path: Path):
    conn = db.init_db(str(tmp_path / "benchmarks.db"))
    conn.execute(
        """INSERT INTO models
           (id, provider, name, slug, cli_model, color, is_active)
           VALUES ('legacy-model', 'legacy', 'Legacy', 'legacy-model', 'legacy', '#000000', 1)"""
    )
    conn.commit()

    db.seed_models_and_categories(conn)

    active_ids = {
        row["id"]
        for row in conn.execute("SELECT id FROM models WHERE is_active = 1").fetchall()
    }
    legacy = conn.execute(
        "SELECT is_active FROM models WHERE id = 'legacy-model'"
    ).fetchone()

    assert active_ids == {model["id"] for model in config.MODELS}
    assert legacy["is_active"] == 0
    conn.close()


def test_reopen_run_clears_derived_state_and_preserves_test_results(tmp_path: Path):
    conn = db.init_db(str(tmp_path / "benchmarks.db"))
    db.seed_models_and_categories(conn)
    run_id = db.create_run(conn, "daily")
    model_id = config.MODELS[0]["id"]
    db.save_test_result(
        conn,
        run_id,
        model_id,
        "bf-1",
        "bug-fixes",
        score=90,
        raw_score=90,
        latency_ms=100,
        token_count=10,
        prompt_tokens=5,
        completion_tokens=5,
        model_output="valid output",
        eval_details={"ok": True},
        error=None,
    )
    db.save_run_scores(conn, run_id, model_id, "bug-fixes", 90, 90, 90, 1)
    db.save_model_run_score(conn, run_id, model_id, 90, 1)
    db.fail_run(conn, run_id, "transient failure")

    assert db.reopen_run(conn, run_id) is True

    run = conn.execute(
        "SELECT status, completed_at, error_log FROM benchmark_runs WHERE id = ?",
        (run_id,),
    ).fetchone()
    assert dict(run) == {
        "status": "running",
        "completed_at": None,
        "error_log": None,
    }
    assert conn.execute(
        "SELECT COUNT(*) FROM test_results WHERE run_id = ?", (run_id,)
    ).fetchone()[0] == 1
    assert conn.execute(
        "SELECT COUNT(*) FROM run_scores WHERE run_id = ?", (run_id,)
    ).fetchone()[0] == 0
    assert conn.execute(
        "SELECT COUNT(*) FROM model_run_scores WHERE run_id = ?", (run_id,)
    ).fetchone()[0] == 0
    conn.close()


def test_reopen_run_refuses_completed_run(tmp_path: Path):
    conn = db.init_db(str(tmp_path / "benchmarks.db"))
    run_id = db.create_run(conn, "daily")
    db.complete_run(conn, run_id, total_tests=1, passed_tests=1)

    assert db.reopen_run(conn, run_id) is False
    run = conn.execute(
        "SELECT status, total_tests, passed_tests FROM benchmark_runs WHERE id = ?",
        (run_id,),
    ).fetchone()
    assert dict(run) == {
        "status": "completed",
        "total_tests": 1,
        "passed_tests": 1,
    }
    conn.close()


def test_resume_helpers_preserve_only_one_successful_result(tmp_path: Path):
    conn = db.init_db(str(tmp_path / "benchmarks.db"))
    db.seed_models_and_categories(conn)
    run_id = db.create_run(conn, "daily")
    model_id = config.MODELS[0]["id"]

    for test_id, score, error in [
        ("bf-1", 90, None),
        ("bf-2", None, "timeout"),
    ]:
        db.save_test_result(
            conn,
            run_id,
            model_id,
            test_id,
            "bug-fixes",
            score=score,
            raw_score=score,
            latency_ms=100,
            token_count=10,
            prompt_tokens=5,
            completion_tokens=5,
            model_output="valid output" if score is not None else None,
            eval_details={"ok": True} if score is not None else None,
            error=error,
        )

    assert db.get_single_success_test_ids(conn, run_id, model_id) == {"bf-1"}
    db.delete_test_results_for_tests(conn, run_id, model_id, ["bf-2"])
    remaining = conn.execute(
        "SELECT test_id FROM test_results WHERE run_id = ? ORDER BY test_id",
        (run_id,),
    ).fetchall()
    assert [row["test_id"] for row in remaining] == ["bf-1"]
    conn.close()
