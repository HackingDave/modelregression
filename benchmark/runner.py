"""
Main benchmark orchestrator.

Runs all tests against all active models via configured model adapters,
scores results, detects regressions, and updates the database.
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

import config
import db
from scoring import aggregate_run_scores, compute_composite_scores
from regression_detector import detect_regressions
from outage_monitor import preflight_check
from openrouter_client import call_chat_completion

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model calls
# ---------------------------------------------------------------------------

def _call_once(
    model_config: dict,
    prompt: str,
    system_prompt: str | None,
) -> tuple[str | None, int | None, int | None, int | None, str | None]:
    """Single attempt to call a model adapter. Returns the raw result tuple."""
    cli = model_config["cli"]

    if cli == "claude":
        return _call_claude(model_config, prompt, system_prompt)
    elif cli == "codex":
        return _call_codex(model_config, prompt, system_prompt)
    elif cli == "agent":
        return _call_grok(model_config, prompt, system_prompt)
    elif cli == "openrouter":
        return _call_openrouter(model_config, prompt, system_prompt)
    else:
        return (None, None, None, None, f"Unknown CLI tool: {cli}")


def _is_retryable(error: str | None) -> bool:
    """Return True if the error is transient and worth retrying."""
    if not error:
        return False
    return any(phrase in error for phrase in (
        "Empty response",
        "HTTP 429",
        "rate limit",
        "temporarily unavailable",
        "unknown error",
        "timed out",
    ))


def call_model(
    model_config: dict,
    prompt: str,
    system_prompt: str | None = None,
) -> tuple[str | None, int | None, int | None, int | None, str | None]:
    """
    Call a model via its configured adapter and return
    (response_text, latency_ms, prompt_tokens, completion_tokens, error).

    Retries up to MAX_RETRIES times on transient failures.
    On success, error is None.
    On failure, response_text is None and error contains the message.
    """
    last_result = None
    for attempt in range(1 + config.MAX_RETRIES):
        try:
            result = _call_once(model_config, prompt, system_prompt)
        except subprocess.TimeoutExpired:
            result = (None, config.CLI_TIMEOUT * 1000, None, None, "CLI call timed out")
        except FileNotFoundError as e:
            return (None, None, None, None, f"CLI tool not found: {e}")
        except Exception as e:
            error_msg = f"{type(e).__name__}: {e}"
            logger.error("CLI call failed for %s: %s", model_config["id"], error_msg)
            result = (None, None, None, None, error_msg)

        last_result = result
        if result[4] is None:
            return result
        if not _is_retryable(result[4]) or attempt == config.MAX_RETRIES:
            return result

        logger.warning("  %s: retry %d/%d after: %s",
                       model_config["id"], attempt + 1, config.MAX_RETRIES, result[4])
        time.sleep(config.RETRY_DELAY)

    return last_result


def _call_claude(
    model_config: dict,
    prompt: str,
    system_prompt: str | None,
) -> tuple[str | None, int, int | None, int | None, str | None]:
    """Call Claude via the claude CLI in print mode with JSON output."""
    cmd = [
        "claude", "-p",
        "--model", model_config["cli_model"],
        "--output-format", "json",
    ]
    if system_prompt:
        cmd.extend(["--system-prompt", system_prompt])

    start = time.monotonic()
    result = subprocess.run(
        cmd,
        input=prompt,
        capture_output=True,
        text=True,
        timeout=config.CLI_TIMEOUT,
    )
    elapsed = int((time.monotonic() - start) * 1000)

    if result.returncode != 0:
        stderr = result.stderr.strip()[:500] if result.stderr else "unknown error"
        return (None, elapsed, None, None, f"claude exited {result.returncode}: {stderr}")

    output = result.stdout.strip()
    if not output:
        return (None, elapsed, None, None, "Empty response from claude")

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

    return (text, elapsed, prompt_tokens, completion_tokens, None)


def _call_codex(
    model_config: dict,
    prompt: str,
    system_prompt: str | None,
) -> tuple[str | None, int, int | None, int | None, str | None]:
    """Call a model via the codex CLI in exec mode."""
    full_prompt = prompt
    if system_prompt:
        full_prompt = f"SYSTEM: {system_prompt}\n\n---\n\n{prompt}"

    cmd = [
        "codex", "exec",
        "-m", model_config["cli_model"],
        "--sandbox", "read-only",
    ]

    start = time.monotonic()
    result = subprocess.run(
        cmd,
        input=full_prompt,
        capture_output=True,
        text=True,
        timeout=config.CLI_TIMEOUT,
    )
    elapsed = int((time.monotonic() - start) * 1000)

    if result.returncode != 0:
        stderr = result.stderr.strip()[:500] if result.stderr else "unknown error"
        return (None, elapsed, None, None, f"codex exited {result.returncode}: {stderr}")

    text = result.stdout.strip()
    if not text:
        return (None, elapsed, None, None, "Empty response from codex")

    return (text, elapsed, None, None, None)


def _call_openrouter(
    model_config: dict,
    prompt: str,
    system_prompt: str | None,
) -> tuple[str | None, int | None, int | None, int | None, str | None]:
    """Call any OpenRouter text model through the chat-completions API."""
    text, latency_ms, prompt_tokens, completion_tokens, error, _http_status = call_chat_completion(
        model_config["cli_model"],
        prompt,
        system_prompt,
        timeout=config.CLI_TIMEOUT,
        supported_parameters=(model_config.get("metadata") or {}).get("supported_parameters"),
    )
    return (text, latency_ms, prompt_tokens, completion_tokens, error)



def _call_grok(
    model_config: dict,
    prompt: str,
    system_prompt: str | None,
) -> tuple[str | None, int, int | None, int | None, str | None]:
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
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=config.CLI_TIMEOUT,
        )
        elapsed = int((time.monotonic() - start) * 1000)

        if result.returncode != 0:
            stderr = result.stderr.strip()[:500] if result.stderr else "unknown error"
            return (None, elapsed, None, None, f"agent exited {result.returncode}: {stderr}")

        output = result.stdout.strip()
        if not output:
            return (None, elapsed, None, None, "Empty response from agent")

        text = output
        try:
            data = json.loads(output)
            text = data.get("text", "")
            if not text and data.get("thought"):
                text = data["thought"]
            if data.get("stopReason") == "Cancelled":
                return (None, elapsed, None, None, "Agent run was cancelled (tool approval needed)")
        except (json.JSONDecodeError, AttributeError):
            pass

        if not text.strip():
            return (None, elapsed, None, None, "Empty response from agent")

        return (text, elapsed, None, None, None)
    finally:
        import os
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
        result = subprocess.run(
            cmd,
            input=prompt,
            capture_output=True,
            text=True,
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

        response_text, latency_ms, prompt_tokens, completion_tokens, error = call_model(
            model_cfg, test_prompt, system_prompt
        )

        if error:
            with _db_lock:
                db.save_test_result(
                    conn, run_id, model_id, test_id, category_id,
                    score=None, raw_score=None, latency_ms=latency_ms,
                    token_count=None, prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    model_output=None, eval_details=None, error=error,
                )
            logger.error("  %s/%s: FAILED - %s", model_id, test_id, error)
            return (False, f"{model_id}/{test_id}: {error}")

        score, eval_details = evaluate_response(test_id, response_text)
        token_count = (prompt_tokens or 0) + (completion_tokens or 0)

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
    parallel_tests = (
        config.OPENROUTER_PARALLEL_TESTS
        if model_cfg["cli"] == "openrouter"
        else config.PARALLEL_TESTS
    )

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


def _openrouter_sweep_summary(model_configs: list[dict], active_tests: list) -> None:
    """Log bounded scope and rough cost for OpenRouter-backed runs."""
    openrouter_models = [m for m in model_configs if m["cli"] == "openrouter"]
    if not openrouter_models:
        return

    benchmark_calls = len(openrouter_models) * len(active_tests)
    logger.info(
        "OpenRouter sweep: %d model(s), %d benchmark calls, up to %d judge calls; "
        "model workers=%d, OpenRouter test workers/model=%d",
        len(openrouter_models),
        benchmark_calls,
        benchmark_calls,
        config.MAX_PARALLEL_MODELS,
        config.OPENROUTER_PARALLEL_TESTS,
    )

    prompt_tokens = int(os.getenv("OPENROUTER_EST_PROMPT_TOKENS", "2000"))
    completion_tokens = int(os.getenv("OPENROUTER_EST_COMPLETION_TOKENS", "1000"))
    cost_estimate = 0.0
    priced_models = 0
    for model in openrouter_models:
        pricing = (model.get("metadata") or {}).get("pricing") or {}
        try:
            prompt_price = float(pricing.get("prompt", 0) or 0)
            completion_price = float(pricing.get("completion", 0) or 0)
        except (TypeError, ValueError):
            continue
        if prompt_price or completion_price:
            priced_models += 1
            cost_estimate += len(active_tests) * (
                prompt_tokens * prompt_price + completion_tokens * completion_price
            )

    if priced_models:
        logger.info(
            "OpenRouter rough model-call cost estimate: $%.4f across %d priced model(s); "
            "judge calls are not included.",
            cost_estimate,
            priced_models,
        )


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

    selected_model_configs = []
    for model_row in active_models:
        model_cfg = config.get_model_by_id(model_row["id"])
        if model_cfg:
            selected_model_configs.append(model_cfg)
        else:
            logger.warning("Active DB model %s has no current config; skipping", model_row["id"])

    db.save_run_model_manifest(conn, run_id, selected_model_configs)
    _openrouter_sweep_summary(selected_model_configs, active_tests)

    total_tests = 0
    passed_tests = 0
    all_errors = []

    try:
        # Run all models in parallel — each uses a different CLI tool
        model_workers = min(len(selected_model_configs), config.MAX_PARALLEL_MODELS)
        with ThreadPoolExecutor(max_workers=max(1, model_workers)) as model_pool:
            model_futures = {}
            for model_cfg in selected_model_configs:
                model_id = model_cfg["id"]
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
