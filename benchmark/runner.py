"""
Main benchmark orchestrator.

Runs all tests against all active models via CLI tools (claude, codex, agent),
scores results, detects regressions, and updates the database.
"""

import argparse
import json
import logging
import os
import signal
import sqlite3
import subprocess
import sys
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from urllib.parse import quote

import config
import db
from scoring import aggregate_run_scores, compute_composite_scores
from regression_detector import detect_regressions
from outage_monitor import preflight_check

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CLI-based model calls
# ---------------------------------------------------------------------------

def _run_cli(cmd, timeout, input=None, **kwargs):
    """Run a CLI subprocess with process-group isolation so timeouts kill the whole tree."""
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE if input is not None else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
        **kwargs,
    )
    try:
        stdout, stderr = proc.communicate(input=input, timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        proc.wait()
        raise
    return subprocess.CompletedProcess(cmd, proc.returncode, stdout, stderr)


_cli_semaphores_lock = threading.Lock()
_cli_semaphores: dict[str, threading.Semaphore] = {}


def _positive_int(value, default: int) -> int:
    """Return a positive integer config value, falling back to the provided default."""
    try:
        number = int(value)
    except (TypeError, ValueError):
        return default
    return number if number > 0 else default


def _model_timeout_seconds(model_config: dict) -> int:
    """Return the timeout for a model CLI call."""
    return _positive_int(model_config.get("timeout_seconds"), config.CLI_TIMEOUT)


def _model_parallel_tests(model_config: dict) -> int:
    """Return the model-specific test concurrency."""
    return _positive_int(model_config.get("parallel_tests"), config.PARALLEL_TESTS)


def _get_cli_semaphore(cli: str) -> threading.Semaphore | None:
    """Return a shared semaphore for a CLI tool when a global limit is configured."""
    limits = getattr(config, "CLI_CONCURRENCY_LIMITS", {})
    try:
        limit = int(limits.get(cli, 0)) if isinstance(limits, dict) else 0
    except (TypeError, ValueError):
        limit = 0
    if limit <= 0:
        return None

    with _cli_semaphores_lock:
        semaphore = _cli_semaphores.get(cli)
        if semaphore is None:
            semaphore = threading.BoundedSemaphore(limit)
            _cli_semaphores[cli] = semaphore
        return semaphore


def _run_cli_with_limit(cli: str, cmd, timeout, input=None, **kwargs):
    """Run a CLI command while respecting the configured global CLI concurrency cap."""
    semaphore = _get_cli_semaphore(cli)
    if semaphore is None:
        return _run_cli(cmd, timeout=timeout, input=input, **kwargs)

    with semaphore:
        return _run_cli(cmd, timeout=timeout, input=input, **kwargs)


def _call_once(
    model_config: dict,
    prompt: str,
    system_prompt: str | None,
) -> tuple[str | None, int | None, int | None, int | None, int | None, str | None]:
    """Single attempt to call a model CLI. Returns the raw result tuple."""
    cli = model_config["cli"]

    if cli == "claude":
        return _call_claude(model_config, prompt, system_prompt)
    elif cli == "codex":
        return _call_codex(model_config, prompt, system_prompt)
    elif cli == "agent":
        return _call_grok(model_config, prompt, system_prompt)
    else:
        return (None, None, None, None, None, f"Unknown CLI tool: {cli}")


def _is_retryable(error: str | None) -> bool:
    """Return True if the error is transient and worth retrying."""
    if not error:
        return False
    return any(phrase in error for phrase in (
        "Empty response",
        "unknown error",
        "timed out",
    ))


def call_model(
    model_config: dict,
    prompt: str,
    system_prompt: str | None = None,
) -> tuple[str | None, int | None, int | None, int | None, int | None, str | None]:
    """
    Call a model via its CLI tool and return
    (response_text, latency_ms, prompt_tokens, completion_tokens, total_tokens, error).

    Retries up to MAX_RETRIES times on transient failures.
    On success, error is None.
    On failure, response_text is None and error contains the message.
    """
    last_result = None
    for attempt in range(1 + config.MAX_RETRIES):
        try:
            result = _call_once(model_config, prompt, system_prompt)
        except subprocess.TimeoutExpired:
            timeout_ms = _model_timeout_seconds(model_config) * 1000
            result = (None, timeout_ms, None, None, None, "CLI call timed out")
        except FileNotFoundError as e:
            return (None, None, None, None, None, f"CLI tool not found: {e}")
        except Exception as e:
            error_msg = f"{type(e).__name__}: {e}"
            logger.error("CLI call failed for %s: %s", model_config["id"], error_msg)
            result = (None, None, None, None, None, error_msg)

        last_result = result
        if result[5] is None:
            return result
        if not _is_retryable(result[5]) or attempt == config.MAX_RETRIES:
            return result

        logger.warning("  %s: retry %d/%d after: %s",
                       model_config["id"], attempt + 1, config.MAX_RETRIES, result[5])
        time.sleep(config.RETRY_DELAY)

    return last_result


def _call_claude(
    model_config: dict,
    prompt: str,
    system_prompt: str | None,
) -> tuple[str | None, int, int | None, int | None, int | None, str | None]:
    """Call Claude via the claude CLI in print mode with JSON output."""
    cmd = [
        "claude", "-p",
        "--model", model_config["cli_model"],
        "--output-format", "json",
    ]
    if system_prompt:
        cmd.extend(["--system-prompt", system_prompt])

    start = time.monotonic()
    result = _run_cli_with_limit(
        model_config["cli"],
        cmd,
        input=prompt,
        timeout=_model_timeout_seconds(model_config),
    )
    elapsed = int((time.monotonic() - start) * 1000)

    if result.returncode != 0:
        stderr = result.stderr.strip()[:500] if result.stderr else "unknown error"
        return (None, elapsed, None, None, None, f"claude exited {result.returncode}: {stderr}")

    output = result.stdout.strip()
    if not output:
        return (None, elapsed, None, None, None, "Empty response from claude")

    prompt_tokens = None
    completion_tokens = None
    text = output

    try:
        data = json.loads(output)
        text = data.get("result", output)
        usage = data.get("usage", {})
        prompt_tokens = usage.get("input_tokens")
        completion_tokens = usage.get("output_tokens")
    except (json.JSONDecodeError, AttributeError):
        pass

    total_tokens = _combine_token_counts(prompt_tokens, completion_tokens)
    return (text, elapsed, prompt_tokens, completion_tokens, total_tokens, None)


def _call_codex(
    model_config: dict,
    prompt: str,
    system_prompt: str | None,
) -> tuple[str | None, int, int | None, int | None, int | None, str | None]:
    """Call a model via the codex CLI in exec mode."""
    full_prompt = prompt
    if system_prompt:
        full_prompt = f"SYSTEM: {system_prompt}\n\n---\n\n{prompt}"

    cmd = [
        "codex", "exec",
        "-m", model_config["cli_model"],
        "--sandbox", "read-only",
        "--json",
    ]

    start = time.monotonic()
    result = _run_cli_with_limit(
        model_config["cli"],
        cmd,
        input=full_prompt,
        timeout=_model_timeout_seconds(model_config),
    )
    elapsed = int((time.monotonic() - start) * 1000)

    if result.returncode != 0:
        stderr = result.stderr.strip()[:500] if result.stderr else "unknown error"
        return (None, elapsed, None, None, None, f"codex exited {result.returncode}: {stderr}")

    output = result.stdout.strip()
    if not output:
        return (None, elapsed, None, None, None, "Empty response from codex")

    text, prompt_tokens, completion_tokens, total_tokens, thread_id = _parse_codex_exec_json(output)
    if total_tokens is None and thread_id:
        prompt_tokens, completion_tokens, total_tokens = _read_codex_usage_from_thread(thread_id)

    if not text:
        return (None, elapsed, prompt_tokens, completion_tokens, total_tokens, "Empty response from codex")

    return (text, elapsed, prompt_tokens, completion_tokens, total_tokens, None)


def _parse_codex_exec_json(
    output: str,
) -> tuple[str, int | None, int | None, int | None, str | None]:
    """Extract the final assistant text and token usage from Codex JSONL."""
    messages: list[str] = []
    prompt_tokens = None
    completion_tokens = None
    total_tokens = None
    thread_id = None

    for line in output.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            data = json.loads(line)
        except (json.JSONDecodeError, AttributeError):
            continue

        event_type = data.get("type")

        if event_type == "thread.started":
            thread_id = data.get("thread_id")
            continue

        if event_type == "item.completed":
            item = data.get("item", {})
            if item.get("type") == "agent_message" and item.get("text"):
                messages.append(item["text"])
            continue

        usage = data.get("usage")
        if usage and event_type in {"turn.completed", "response.completed", "response.complete"}:
            prompt_tokens, completion_tokens, total_tokens = _extract_usage_fields(usage)

    text = "\n\n".join(msg.strip() for msg in messages if msg and msg.strip())
    return (text, prompt_tokens, completion_tokens, total_tokens, thread_id)


def _combine_token_counts(
    prompt_tokens: int | None,
    completion_tokens: int | None,
) -> int | None:
    """Return the total token count, or None if usage was not provided."""
    if prompt_tokens is None and completion_tokens is None:
        return None
    return (prompt_tokens or 0) + (completion_tokens or 0)


def _extract_usage_fields(
    usage: dict | None,
) -> tuple[int | None, int | None, int | None]:
    """Normalize token usage fields from different CLI event shapes."""
    if not isinstance(usage, dict):
        return (None, None, None)

    prompt_tokens = usage.get("input_tokens") or usage.get("prompt_tokens")
    completion_tokens = usage.get("output_tokens") or usage.get("completion_tokens")
    total_tokens = usage.get("total_tokens")
    if total_tokens is None:
        total_tokens = _combine_token_counts(prompt_tokens, completion_tokens)

    return (prompt_tokens, completion_tokens, total_tokens)


def _read_codex_usage_from_thread(
    thread_id: str,
) -> tuple[int | None, int | None, int | None]:
    """Read Codex token usage from the persisted thread rollout when stdout omits it."""
    db_path = os.path.expanduser("~/.codex/state_5.sqlite")
    if not os.path.exists(db_path):
        return (None, None, None)

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT rollout_path, tokens_used FROM threads WHERE id = ?",
            (thread_id,),
        ).fetchone()
        if not row:
            return (None, None, None)

        rollout_path = row["rollout_path"]
        if rollout_path and os.path.exists(rollout_path):
            with open(rollout_path) as handle:
                for line in handle:
                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    payload = event.get("payload", {})
                    if payload.get("type") != "token_count":
                        continue
                    info = payload.get("info") or {}
                    usage = info.get("last_token_usage") or info.get("total_token_usage")
                    prompt_tokens, completion_tokens, total_tokens = _extract_usage_fields(usage)
                    if total_tokens is not None:
                        return (prompt_tokens, completion_tokens, total_tokens)

        total_tokens = row["tokens_used"] if row["tokens_used"] else None
        return (None, None, total_tokens)
    except sqlite3.Error as exc:
        logger.debug("Failed to read Codex usage fallback for %s: %s", thread_id, exc)
        return (None, None, None)
    finally:
        try:
            conn.close()
        except UnboundLocalError:
            pass


def _extract_user_query(text: str) -> str:
    """Extract the wrapped user query body from Grok chat/session content."""
    start_tag = "<user_query>"
    end_tag = "</user_query>"
    start = text.find(start_tag)
    end = text.find(end_tag)
    if start == -1 or end == -1 or end <= start:
        return text.strip()
    return text[start + len(start_tag):end].strip()


def _read_grok_usage_from_session(
    session_id: str,
    request_id: str | None,
    cwd: str | None = None,
) -> int | None:
    """Read Grok total token burn for a headless session from its persisted updates."""
    session_cwd = cwd or os.getcwd()
    session_root = os.path.expanduser("~/.grok/sessions")
    session_dir = os.path.join(session_root, quote(session_cwd, safe=""), session_id)
    updates_path = os.path.join(session_dir, "updates.jsonl")
    if not os.path.exists(updates_path):
        return None

    baseline_total = None
    prompt_total = None

    try:
        with open(updates_path) as handle:
            for line in handle:
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue

                meta = event.get("params", {}).get("_meta", {})
                total_tokens = meta.get("totalTokens")
                prompt_id = meta.get("promptId")
                if total_tokens is None:
                    continue

                if request_id and prompt_id == request_id:
                    prompt_total = total_tokens if prompt_total is None else max(prompt_total, total_tokens)
                elif prompt_id is None:
                    baseline_total = total_tokens if baseline_total is None else max(baseline_total, total_tokens)
    except OSError as exc:
        logger.debug("Failed to read Grok usage fallback for %s: %s", session_id, exc)
        return None

    if prompt_total is None:
        return None

    baseline_total = baseline_total or 0
    total_tokens = prompt_total - baseline_total
    return total_tokens if total_tokens > 0 else prompt_total



def _call_grok(
    model_config: dict,
    prompt: str,
    system_prompt: str | None,
) -> tuple[str | None, int, int | None, int | None, int | None, str | None]:
    """Call Grok via the agent CLI in single-shot mode."""
    import tempfile
    prompt_file = tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False,
    )
    try:
        prompt_file.write(prompt)
        prompt_file.close()
        cmd = [
            "agent",
            "--prompt-file", prompt_file.name,
            "-m", model_config["cli_model"],
            "--output-format", "json",
            "--always-approve",
        ]
        if system_prompt:
            cmd.extend(["--system-prompt", system_prompt])

        start = time.monotonic()
        result = _run_cli_with_limit(
            model_config["cli"],
            cmd,
            timeout=_model_timeout_seconds(model_config),
        )
        elapsed = int((time.monotonic() - start) * 1000)

        if result.returncode != 0:
            stderr = result.stderr.strip()[:500] if result.stderr else "unknown error"
            return (None, elapsed, None, None, None, f"agent exited {result.returncode}: {stderr}")

        output = result.stdout.strip()
        if not output:
            return (None, elapsed, None, None, None, "Empty response from agent")

        text = output
        prompt_tokens = None
        completion_tokens = None
        total_tokens = None
        session_id = None
        request_id = None
        try:
            data = json.loads(output)
            text = data.get("text", "")
            if not text and data.get("thought"):
                text = data["thought"]
            if data.get("stopReason") == "Cancelled":
                return (None, elapsed, None, None, None, "Agent run was cancelled (tool approval needed)")
            usage = data.get("usage")
            prompt_tokens, completion_tokens, total_tokens = _extract_usage_fields(usage)
            session_id = data.get("sessionId")
            request_id = data.get("requestId")
        except (json.JSONDecodeError, AttributeError):
            pass

        if total_tokens is None and session_id:
            total_tokens = _read_grok_usage_from_session(session_id, request_id, os.getcwd())

        if not text.strip():
            return (None, elapsed, prompt_tokens, completion_tokens, total_tokens, "Empty response from agent")

        return (text, elapsed, prompt_tokens, completion_tokens, total_tokens, None)
    finally:
        os.unlink(prompt_file.name)


# ---------------------------------------------------------------------------
# Test registry — maps test IDs to actual test class instances with
# prompts, rubrics, and evaluation logic from benchmark/tests/
# ---------------------------------------------------------------------------

from tests import ALL_TESTS

TEST_REGISTRY: dict = {t.id: t for t in ALL_TESTS}


def _judge_fn(prompt: str) -> str | None:
    """LLM judge callback — uses Claude (via CLI) to evaluate model outputs."""
    cmd = ["claude", "-p", "--model", "sonnet"]
    try:
        result = _run_cli_with_limit(
            "claude",
            cmd,
            input=prompt,
            timeout=config.CLI_TIMEOUT,
        )
        if result.returncode != 0:
            logger.warning("Judge returned exit code %d", result.returncode)
            return None
        return result.stdout.strip() or None
    except Exception as e:
        logger.warning("Judge call failed: %s", e)
        return None


def evaluate_response(test_id: str, model_output: str) -> tuple[float, dict]:
    """
    Evaluate a model's output using the test's real evaluation logic.

    Dispatches to regex, llm_judge, or composite evaluators defined in
    benchmark/tests/ based on the test class.
    """
    if not model_output or len(model_output.strip()) < 10:
        return (0.0, {"reason": "empty_or_too_short"})

    test_instance = TEST_REGISTRY.get(test_id)
    if not test_instance:
        logger.warning("No test instance found for %s, falling back to length-based scoring", test_id)
        base_score = min(85.0, 50.0 + len(model_output) / 200)
        return (round(base_score, 1), {"eval_type": "fallback", "output_length": len(model_output)})

    eval_result = test_instance.evaluate(model_output, judge_fn=_judge_fn)
    return (round(eval_result.score, 1), eval_result.details)


# ---------------------------------------------------------------------------
# Main orchestrator — parallelized
# ---------------------------------------------------------------------------

_db_lock = threading.Lock()


def _run_single_test(
    model_cfg: dict,
    test_row: dict,
    run_id: str,
    conn,
) -> tuple[bool, str | None]:
    """
    Run one test for one model: call the model, evaluate, save result.

    Returns (passed, error_string_or_none).
    Thread-safe — uses _db_lock for DB writes.
    """
    model_id = model_cfg["id"]
    test_id = test_row["id"]
    category_id = test_row["category_id"]

    try:
        test_instance = TEST_REGISTRY.get(test_id)
        test_prompt = (
            test_instance.prompt if test_instance
            else test_row.get("prompt") or test_row["description"]
        )
        system_prompt = (
            test_instance.system_prompt if test_instance
            else "You are being evaluated on a coding/reasoning benchmark. "
                 "Provide thorough, correct, and well-structured responses."
        )

        response_text, latency_ms, prompt_tokens, completion_tokens, total_tokens, error = call_model(
            model_cfg, test_prompt, system_prompt
        )

        if error:
            with _db_lock:
                db.save_test_result(
                    conn, run_id, model_id, test_id, category_id,
                    score=None, raw_score=None, latency_ms=latency_ms,
                    token_count=total_tokens, prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    model_output=None, eval_details=None, error=error,
                )
            logger.error("  %s/%s: FAILED - %s", model_id, test_id, error)
            return (False, f"{model_id}/{test_id}: {error}")

        score, eval_details = evaluate_response(test_id, response_text)
        token_count = total_tokens if total_tokens is not None else _combine_token_counts(prompt_tokens, completion_tokens)

        with _db_lock:
            db.save_test_result(
                conn, run_id, model_id, test_id, category_id,
                score=score, raw_score=score, latency_ms=latency_ms,
                token_count=token_count, prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                model_output=response_text, eval_details=eval_details,
                error=None,
            )
        logger.info("  %s/%s: score=%.1f latency=%dms", model_id, test_id, score, latency_ms or 0)
        return (True, None)

    except Exception as e:
        error_msg = f"{type(e).__name__}: {e}"
        logger.error("  %s/%s: EXCEPTION - %s", model_id, test_id, error_msg)
        logger.debug(traceback.format_exc())
        with _db_lock:
            db.save_test_result(
                conn, run_id, model_id, test_id, category_id,
                score=None, raw_score=None, latency_ms=None,
                token_count=None, prompt_tokens=None, completion_tokens=None,
                model_output=None, eval_details=None, error=error_msg,
            )
        return (False, f"{model_id}/{test_id}: {error_msg}")


def _run_model_tests(
    model_cfg: dict,
    active_tests: list,
    run_id: str,
    conn,
) -> tuple[int, int, list[str]]:
    """
    Run all tests for a single model using a thread pool.

    Returns (total, passed, errors).
    """
    model_id = model_cfg["id"]
    total = len(active_tests)
    passed = 0
    errors = []
    parallel_tests = _model_parallel_tests(model_cfg)

    logger.info("Testing model: %s (%s via %s) — %d tests, %d parallel",
                model_cfg["name"], model_cfg["cli_model"], model_cfg["cli"],
                total, parallel_tests)

    with ThreadPoolExecutor(max_workers=parallel_tests) as pool:
        futures = {
            pool.submit(_run_single_test, model_cfg, test_row, run_id, conn): test_row
            for test_row in active_tests
        }
        for future in as_completed(futures):
            ok, err = future.result()
            if ok:
                passed += 1
            if err:
                errors.append(err)

    logger.info("  %s done: %d/%d passed", model_id, passed, total)
    return (total, passed, errors)


def run_benchmarks(schedule: str, model_filter: str | None = None) -> None:
    """Execute a full benchmark run with parallel test execution."""
    logger.info("Starting benchmark run (schedule=%s, parallel=%d, model=%s)",
                schedule, config.PARALLEL_TESTS, model_filter or "all")

    conn = db.init_db()
    db.seed_models_and_categories(conn)

    logger.info("Running outage pre-flight check...")
    outage_results = preflight_check(conn)
    for model_id, is_up in outage_results.items():
        if not is_up:
            logger.warning("Model %s failed pre-flight check", model_id)

    run_id = db.create_run(conn, schedule)
    logger.info("Created benchmark run: %s", run_id)

    active_models = db.get_active_models(conn)
    active_tests = db.get_active_tests(conn)

    # Filter to a single model when requested
    if model_filter:
        active_models = [m for m in active_models if m["id"] == model_filter]
        if not active_models:
            logger.error("Model %s not found or not active", model_filter)
            db.complete_run(conn, run_id, 0, 0, f"Model {model_filter} not found")
            conn.close()
            return

    total_tests = 0
    passed_tests = 0
    all_errors = []

    try:
        # Run all models in parallel — each uses a different CLI tool
        with ThreadPoolExecutor(max_workers=len(active_models)) as model_pool:
            model_futures = {}
            for model_row in active_models:
                model_id = model_row["id"]
                model_cfg = config.get_model_by_id(model_id)
                if not model_cfg:
                    logger.error("No config found for model %s", model_id)
                    continue

                open_outage = db.get_open_outage(conn, model_id)
                if open_outage and open_outage["check_count"] >= 3:
                    logger.warning("Skipping model %s (in outage since %s)", model_id, open_outage["started_at"])
                    continue

                future = model_pool.submit(_run_model_tests, model_cfg, active_tests, run_id, conn)
                model_futures[future] = model_cfg["name"]

            for future in as_completed(model_futures):
                name = model_futures[future]
                try:
                    total, passed, errors = future.result()
                    total_tests += total
                    passed_tests += passed
                    all_errors.extend(errors)
                except Exception as e:
                    logger.error("Model %s crashed: %s", name, e)
                    all_errors.append(f"{name}: {e}")

        logger.info("Aggregating scores...")
        aggregate_run_scores(conn, run_id)

        logger.info("Computing composite scores...")
        compute_composite_scores(conn, run_id)

        logger.info("Running regression detection...")
        detect_regressions(conn, run_id)

        error_log = "\n".join(all_errors) if all_errors else None
        db.complete_run(conn, run_id, total_tests, passed_tests, error_log)

        logger.info(
            "Benchmark run complete: %d/%d tests passed (%d errors)",
            passed_tests, total_tests, len(all_errors),
        )
    except Exception as e:
        logger.error("Benchmark run crashed: %s", e)
        db.complete_run(conn, run_id, total_tests, passed_tests, str(e))
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Run ModelRegression benchmarks")
    parser.add_argument(
        "--schedule",
        choices=["daily", "morning", "afternoon", "night"],
        default="daily",
        help="Schedule label for this run (default: daily)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Run only a specific model by ID (e.g., grok, claude-opus-4-8)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable debug logging",
    )
    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    try:
        run_benchmarks(args.schedule, model_filter=args.model)
    except Exception as e:
        logger.critical("Benchmark run failed: %s", e)
        logger.debug(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
