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
