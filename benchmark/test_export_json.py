from pathlib import Path
import json
import sys

BENCHMARK_DIR = Path(__file__).resolve().parent
if str(BENCHMARK_DIR) not in sys.path:
    sys.path.insert(0, str(BENCHMARK_DIR))

import db
import config
import export_json

OPUS_MODEL = next(model for model in config.MODELS if model["cli"] == "claude")
CODEX_MODEL = next(model for model in config.MODELS if model["cli"] == "codex")
OPUS_ID = OPUS_MODEL["id"]
CODEX_ID = CODEX_MODEL["id"]


def _seed_run_with_tokens(tmp_path: Path):
    conn = db.init_db(str(tmp_path / "benchmarks.db"))
    db.seed_models_and_categories(conn)

    run_id = db.create_run(conn, "daily")
    model_id = OPUS_ID
    category_id = "bug-fixes"

    db.save_test_result(
        conn,
        run_id,
        model_id,
        "bf-1",
        category_id,
        score=91,
        raw_score=91,
        latency_ms=1200,
        token_count=100,
        prompt_tokens=60,
        completion_tokens=40,
        model_output="fixed",
        eval_details={"grade": "A"},
        error=None,
    )
    db.save_test_result(
        conn,
        run_id,
        model_id,
        "bf-2",
        category_id,
        score=95,
        raw_score=95,
        latency_ms=1300,
        token_count=200,
        prompt_tokens=120,
        completion_tokens=80,
        model_output="fixed",
        eval_details={"grade": "A"},
        error=None,
    )
    db.save_test_result(
        conn,
        run_id,
        model_id,
        "bf-3",
        category_id,
        score=97,
        raw_score=97,
        latency_ms=1400,
        token_count=None,
        prompt_tokens=None,
        completion_tokens=None,
        model_output="fixed",
        eval_details={"grade": "A"},
        error=None,
    )

    db.save_run_scores(conn, run_id, model_id, category_id, 94.3, 91, 97, 3)
    db.save_run_scores(conn, run_id, model_id, "token-efficiency", 100, 100, 100, 2)
    db.save_model_run_score(conn, run_id, model_id, 94.3, 1)
    db.complete_run(conn, run_id, total_tests=3, passed_tests=3)
    return conn


def test_export_latest_includes_total_and_average_tokens(tmp_path):
    conn = _seed_run_with_tokens(tmp_path)
    output_dir = tmp_path / "out"

    export_json.export_latest(conn, str(output_dir))

    data = json.loads((output_dir / "latest.json").read_text())
    model = data["models"][OPUS_MODEL["slug"]]
    tests = {
        item["testId"]: item["tokenCount"]
        for item in model["categories"]["bug-fixes"]["tests"]
    }

    assert model["totalTokens"] == 300
    assert model["avgTokensPerTest"] == 150
    assert tests == {"bf-1": 100, "bf-2": 200, "bf-3": None}


def test_export_latest_includes_failed_tests_as_zero(tmp_path):
    conn = db.init_db(str(tmp_path / "benchmarks.db"))
    db.seed_models_and_categories(conn)
    run_id = db.create_run(conn, "daily")
    model_id = CODEX_ID

    db.save_test_result(
        conn,
        run_id,
        model_id,
        "bf-1",
        "bug-fixes",
        score=100,
        raw_score=100,
        latency_ms=1000,
        token_count=100,
        prompt_tokens=50,
        completion_tokens=50,
        model_output="fixed",
        eval_details={"grade": "A"},
        error=None,
    )
    db.save_test_result(
        conn,
        run_id,
        model_id,
        "bf-2",
        "bug-fixes",
        score=None,
        raw_score=None,
        latency_ms=None,
        token_count=None,
        prompt_tokens=None,
        completion_tokens=None,
        model_output=None,
        eval_details=None,
        error="CLI call timed out",
    )
    db.save_run_scores(conn, run_id, model_id, "bug-fixes", 50, 0, 100, 2)
    db.save_model_run_score(conn, run_id, model_id, 50, 1)
    db.complete_run(conn, run_id, total_tests=2, passed_tests=1)

    output_dir = tmp_path / "out"
    export_json.export_latest(conn, str(output_dir))

    data = json.loads((output_dir / "latest.json").read_text())
    tests = {
        item["testId"]: item["score"]
        for item in data["models"][CODEX_MODEL["slug"]]["categories"]["bug-fixes"]["tests"]
    }

    assert tests == {"bf-1": 100, "bf-2": 0}


def test_export_evidence_includes_prompt_and_completion_tokens(tmp_path):
    conn = _seed_run_with_tokens(tmp_path)
    output_dir = tmp_path / "out"

    export_json.export_evidence(conn, str(output_dir))

    evidence_dir = output_dir / "evidence"
    run_dir = next(evidence_dir.iterdir())
    data = json.loads((run_dir / "bf-1.json").read_text())
    result = data["results"][OPUS_ID]

    assert result["tokenCount"] == 100
    assert result["promptTokens"] == 60
    assert result["completionTokens"] == 40


def test_export_token_efficiency_category_includes_average_tokens(tmp_path):
    conn = _seed_run_with_tokens(tmp_path)
    output_dir = tmp_path / "out"

    export_json.export_categories(conn, str(output_dir))

    data = json.loads((output_dir / "categories" / "token-efficiency.json").read_text())
    model = data["models"][OPUS_MODEL["slug"]]

    assert model["currentScore"] == 100
    assert model["totalTokens"] == 300
    assert model["avgTokensPerTest"] == 150


def test_export_category_includes_actual_per_test_scores(tmp_path):
    conn = _seed_run_with_tokens(tmp_path)
    output_dir = tmp_path / "out"

    export_json.export_categories(conn, str(output_dir))

    data = json.loads((output_dir / "categories" / "bug-fixes.json").read_text())
    scores = data["models"][OPUS_MODEL["slug"]]["testScores"]

    assert scores == {"bf-1": 91, "bf-2": 95, "bf-3": 97}


def _seed_mixed_latest_runs(tmp_path: Path):
    conn = db.init_db(str(tmp_path / "benchmarks.db"))
    db.seed_models_and_categories(conn)

    def save_result(
        run_id: str,
        model_id: str,
        test_id: str,
        score: float,
        tokens: int,
    ) -> None:
        db.save_test_result(
            conn,
            run_id,
            model_id,
            test_id,
            "bug-fixes",
            score=score,
            raw_score=score,
            latency_ms=1200,
            token_count=tokens,
            prompt_tokens=tokens // 2,
            completion_tokens=tokens - (tokens // 2),
            model_output="fixed",
            eval_details={"grade": "A"},
            error=None,
        )

    run1 = db.create_run(conn, "daily")
    save_result(run1, OPUS_ID, "bf-1", 90, 100)
    save_result(run1, "grok", "bf-1", 95, 200)
    db.save_run_scores(conn, run1, OPUS_ID, "bug-fixes", 90, 90, 90, 1)
    db.save_run_scores(conn, run1, OPUS_ID, "token-efficiency", 100, 100, 100, 1)
    db.save_model_run_score(conn, run1, OPUS_ID, 95, 1)
    db.save_run_scores(conn, run1, "grok", "bug-fixes", 95, 95, 95, 1)
    db.save_run_scores(conn, run1, "grok", "token-efficiency", 50, 50, 50, 1)
    db.save_model_run_score(conn, run1, "grok", 72.5, 2)
    db.complete_run(conn, run1, total_tests=2, passed_tests=2)
    conn.execute(
        "UPDATE benchmark_runs SET started_at = ?, completed_at = ? WHERE id = ?",
        ("2026-06-05T10:00:00+00:00", "2026-06-05T10:05:00+00:00", run1),
    )

    run2 = db.create_run(conn, "daily")
    save_result(run2, "grok", "bf-1", 95, 400)
    db.save_run_scores(conn, run2, "grok", "bug-fixes", 95, 95, 95, 1)
    db.save_run_scores(conn, run2, "grok", "token-efficiency", 100, 100, 100, 1)
    db.save_model_run_score(conn, run2, "grok", 97.5, 1)
    db.complete_run(conn, run2, total_tests=1, passed_tests=1)
    conn.execute(
        "UPDATE benchmark_runs SET started_at = ?, completed_at = ? WHERE id = ?",
        ("2026-06-05T12:00:00+00:00", "2026-06-05T12:05:00+00:00", run2),
    )
    conn.commit()

    return conn


def _use_two_model_catalog(monkeypatch, *model_ids: str) -> None:
    monkeypatch.setattr(
        export_json.config,
        "MODELS",
        [model for model in config.MODELS if model["id"] in model_ids],
    )


def test_export_latest_recomputes_token_efficiency_across_composed_runs(tmp_path, monkeypatch):
    conn = _seed_mixed_latest_runs(tmp_path)
    _use_two_model_catalog(monkeypatch, OPUS_ID, "grok")
    output_dir = tmp_path / "out"

    export_json.export_latest(conn, str(output_dir))

    data = json.loads((output_dir / "latest.json").read_text())
    claude = data["models"][OPUS_MODEL["slug"]]
    grok = data["models"]["grok"]

    assert claude["categories"]["token-efficiency"]["avgScore"] == 100
    assert grok["categories"]["token-efficiency"]["avgScore"] == 25
    assert claude["compositeScore"] == 95
    assert grok["compositeScore"] == 60
    assert claude["rank"] == 1
    assert grok["rank"] == 2


def test_export_latest_recomputed_composite_counts_missing_category_as_zero(tmp_path, monkeypatch):
    conn = db.init_db(str(tmp_path / "benchmarks.db"))
    db.seed_models_and_categories(conn)
    run_id = db.create_run(conn, "daily")

    db.save_run_scores(conn, run_id, OPUS_ID, "bug-fixes", 100, 100, 100, 1)
    db.save_run_scores(conn, run_id, OPUS_ID, "security-awareness", 100, 100, 100, 1)
    db.save_model_run_score(conn, run_id, OPUS_ID, 100, 1)

    db.save_run_scores(conn, run_id, CODEX_ID, "bug-fixes", 100, 100, 100, 1)
    db.save_model_run_score(conn, run_id, CODEX_ID, 100, 2)
    db.complete_run(conn, run_id, total_tests=3, passed_tests=3)
    _use_two_model_catalog(monkeypatch, OPUS_ID, CODEX_ID)

    output_dir = tmp_path / "out"
    export_json.export_latest(conn, str(output_dir))

    data = json.loads((output_dir / "latest.json").read_text())

    assert data["models"][OPUS_MODEL["slug"]]["compositeScore"] == 100
    assert data["models"][CODEX_MODEL["slug"]]["compositeScore"] == 50
    assert data["models"][OPUS_MODEL["slug"]]["rank"] == 1
    assert data["models"][CODEX_MODEL["slug"]]["rank"] == 2


def test_export_categories_uses_recomputed_current_token_efficiency(tmp_path, monkeypatch):
    conn = _seed_mixed_latest_runs(tmp_path)
    _use_two_model_catalog(monkeypatch, OPUS_ID, "grok")
    output_dir = tmp_path / "out"

    export_json.export_categories(conn, str(output_dir))

    data = json.loads((output_dir / "categories" / "token-efficiency.json").read_text())

    assert data["models"][OPUS_MODEL["slug"]]["currentScore"] == 100
    assert data["models"][OPUS_MODEL["slug"]]["avgTokensPerTest"] == 100
    assert data["models"]["grok"]["currentScore"] == 25
    assert data["models"]["grok"]["avgTokensPerTest"] == 400


def test_export_daily_trends_recomputes_composed_day_snapshot(tmp_path, monkeypatch):
    conn = _seed_mixed_latest_runs(tmp_path)
    _use_two_model_catalog(monkeypatch, OPUS_ID, "grok")
    output_dir = tmp_path / "out"

    export_json.export_trends(conn, str(output_dir))

    data = json.loads((output_dir / "trends" / "daily.json").read_text())
    day = data["data"][0]["models"]

    assert day[OPUS_MODEL["slug"]] == 95
    assert day["grok"] == 60


def test_export_synopsis_day_uses_latest_valid_run_when_recent_runs_failed(tmp_path):
    conn = db.init_db(str(tmp_path / "benchmarks.db"))
    db.seed_models_and_categories(conn)

    prev_run = db.create_run(conn, "daily")
    db.save_model_run_score(conn, prev_run, OPUS_ID, 90, 1)
    db.save_model_run_score(conn, prev_run, CODEX_ID, 80, 2)
    db.complete_run(conn, prev_run, total_tests=2, passed_tests=2)
    conn.execute(
        "UPDATE benchmark_runs SET started_at = ?, completed_at = ? WHERE id = ?",
        ("2026-06-29T03:00:00+00:00", "2026-06-29T04:00:00+00:00", prev_run),
    )

    latest_valid = db.create_run(conn, "daily")
    db.save_model_run_score(conn, latest_valid, OPUS_ID, 92.3, 1)
    db.save_model_run_score(conn, latest_valid, CODEX_ID, 89.3, 2)
    db.complete_run(conn, latest_valid, total_tests=2, passed_tests=2)
    conn.execute(
        "UPDATE benchmark_runs SET started_at = ?, completed_at = ? WHERE id = ?",
        ("2026-06-30T03:00:00+00:00", "2026-06-30T04:00:00+00:00", latest_valid),
    )

    failed_run = db.create_run(conn, "daily")
    conn.execute(
        """UPDATE benchmark_runs
           SET started_at = ?, completed_at = ?, status = ?, total_tests = ?, passed_tests = ?
           WHERE id = ?""",
        (
            "2026-07-02T03:00:00+00:00",
            "2026-07-02T03:05:00+00:00",
            "failed",
            2,
            0,
            failed_run,
        ),
    )
    conn.commit()

    output_dir = tmp_path / "out"
    export_json.export_synopsis(conn, str(output_dir))

    data = json.loads((output_dir / "synopsis.json").read_text())

    assert data["day"] == {
        "modelId": OPUS_MODEL["slug"],
        "name": OPUS_MODEL["name"],
        "score": 92.3,
        "change": 2.3,
    }


def test_export_model_catalog_matches_runtime_models(tmp_path):
    export_json.export_model_catalog(str(tmp_path))

    catalog = json.loads((tmp_path / "model-catalog.json").read_text())

    assert [model["id"] for model in catalog] == [
        model["id"] for model in config.MODELS
    ]
    assert {model["provider"] for model in catalog} == {
        "anthropic",
        "openai",
        "xai",
    }


def test_public_outage_message_removes_cli_diagnostics():
    raw = (
        "codex exited 1: workdir: /home/user/private model: gpt-5.5 "
        "session id: secret-session"
    )

    public = export_json._public_outage_message("error", raw)

    assert public == "Provider CLI request failed"
    assert "/home/" not in public
    assert "session" not in public.lower()
