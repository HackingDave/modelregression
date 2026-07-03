from pathlib import Path
import json
import sqlite3
import sys
from types import SimpleNamespace

import pytest

BENCHMARK_DIR = Path(__file__).resolve().parent
if str(BENCHMARK_DIR) not in sys.path:
    sys.path.insert(0, str(BENCHMARK_DIR))

import runner


def test_call_codex_parses_json_output_and_usage(monkeypatch):
    captured: dict[str, object] = {}
    stdout = "\n".join(
        [
            '{"type":"thread.started","thread_id":"thread_123"}',
            '{"type":"turn.started"}',
            '{"type":"item.completed","item":{"id":"item_0","type":"agent_message","text":"ok"}}',
            '{"type":"turn.completed","usage":{"input_tokens":11072,"cached_input_tokens":9600,"output_tokens":23,"reasoning_output_tokens":16}}',
        ]
    )

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        captured["kwargs"] = kwargs
        return SimpleNamespace(returncode=0, stdout=stdout, stderr="")

    times = iter([10.0, 10.25])
    monkeypatch.setattr(runner, "_run_cli", fake_run)
    monkeypatch.setattr(runner.time, "monotonic", lambda: next(times))

    text, latency_ms, prompt_tokens, completion_tokens, total_tokens, error = runner._call_codex(
        {"cli": "codex", "cli_model": "gpt-5.5"},
        "Reply with exactly: ok",
        None,
    )

    assert "--json" in captured["cmd"]
    assert text == "ok"
    assert latency_ms == 250
    assert prompt_tokens == 11072
    assert completion_tokens == 23
    assert total_tokens == 11095
    assert error is None


def test_combine_token_counts_returns_none_when_usage_missing():
    assert runner._combine_token_counts(None, None) is None
    assert runner._combine_token_counts(12, None) == 12
    assert runner._combine_token_counts(None, 34) == 34
    assert runner._combine_token_counts(12, 34) == 46


def test_read_codex_usage_from_thread_reads_rollout_token_event(tmp_path, monkeypatch):
    home = tmp_path / "home"
    codex_dir = home / ".codex"
    sessions_dir = codex_dir / "sessions" / "2026" / "06" / "05"
    sessions_dir.mkdir(parents=True)

    rollout_path = sessions_dir / "rollout.jsonl"
    rollout_path.write_text(
        "\n".join(
            [
                json.dumps({"type": "session_meta", "payload": {"id": "thread-1"}}),
                json.dumps(
                    {
                        "type": "event_msg",
                        "payload": {
                            "type": "token_count",
                            "info": {
                                "last_token_usage": {
                                    "input_tokens": 120,
                                    "output_tokens": 30,
                                    "total_tokens": 150,
                                }
                            },
                        },
                    }
                ),
            ]
        )
    )

    db_path = codex_dir / "state_5.sqlite"
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE threads (id TEXT PRIMARY KEY, rollout_path TEXT, tokens_used INTEGER)"
    )
    conn.execute(
        "INSERT INTO threads (id, rollout_path, tokens_used) VALUES (?, ?, ?)",
        ("thread-1", str(rollout_path), 150),
    )
    conn.commit()
    conn.close()

    monkeypatch.setenv("HOME", str(home))

    prompt_tokens, completion_tokens, total_tokens = runner._read_codex_usage_from_thread("thread-1")

    assert prompt_tokens == 120
    assert completion_tokens == 30
    assert total_tokens == 150


def test_read_grok_usage_from_session_uses_prompt_delta(tmp_path, monkeypatch):
    home = tmp_path / "home"
    session_id = "session-1"
    request_id = "request-1"
    session_dir = (
        home
        / ".grok"
        / "sessions"
        / "%2Ftmp%2Fbenchmark"
        / session_id
    )
    session_dir.mkdir(parents=True)

    updates = [
        {
            "params": {
                "_meta": {
                    "totalTokens": 3692,
                }
            }
        },
        {
            "params": {
                "_meta": {
                    "promptId": request_id,
                    "totalTokens": 3706,
                }
            }
        },
        {
            "params": {
                "_meta": {
                    "promptId": request_id,
                    "totalTokens": 15269,
                }
            }
        },
    ]
    (session_dir / "updates.jsonl").write_text("\n".join(json.dumps(item) for item in updates))

    monkeypatch.setenv("HOME", str(home))

    total_tokens = runner._read_grok_usage_from_session(session_id, request_id, "/tmp/benchmark")

    assert total_tokens == 11577


def test_call_model_reports_model_specific_timeout(monkeypatch):
    model_config = {
        "id": "claude-sonnet-4-6",
        "cli": "claude",
        "timeout_seconds": 900,
    }

    def fake_call_once(*_args, **_kwargs):
        raise runner.subprocess.TimeoutExpired(cmd=["claude"], timeout=900)

    monkeypatch.setattr(runner.config, "MAX_RETRIES", 0)
    monkeypatch.setattr(runner, "_call_once", fake_call_once)

    text, latency_ms, prompt_tokens, completion_tokens, total_tokens, error = runner.call_model(
        model_config,
        "prompt",
    )

    assert text is None
    assert latency_ms == 900000
    assert prompt_tokens is None
    assert completion_tokens is None
    assert total_tokens is None
    assert error == "CLI call timed out"


def test_model_parallel_tests_uses_model_override():
    assert runner._model_parallel_tests({"parallel_tests": 2}) == 2
    assert runner._model_parallel_tests({"parallel_tests": 0}) == runner.config.PARALLEL_TESTS
    assert runner._model_parallel_tests({}) == runner.config.PARALLEL_TESTS


def test_details_contain_error_finds_nested_judge_failure():
    details = {
        "regex_score": 100.0,
        "judge_details": {
            "error": "judge_call_failed",
        },
    }

    assert runner._details_contain_error(details, "judge_call_failed")


def test_evaluate_response_raises_when_judge_fails(monkeypatch):
    class FakeTest:
        eval_type = "composite"

        def evaluate(self, _model_output, judge_fn=None):
            return SimpleNamespace(
                score=40.0,
                details={
                    "regex_score": 100.0,
                    "judge_score": 0.0,
                    "judge_details": {"error": "judge_call_failed"},
                },
            )

    monkeypatch.setitem(runner.TEST_REGISTRY, "fake-judge-test", FakeTest())

    with pytest.raises(runner.EvaluationFailed) as exc:
        runner.evaluate_response("fake-judge-test", "model output long enough")

    assert exc.value.reason == "judge_call_failed"
