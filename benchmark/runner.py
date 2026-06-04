"""
Main benchmark orchestrator.

Runs all tests against all active models, scores results,
detects regressions, and updates the database.
"""

import argparse
import logging
import sys
import time
import traceback
from datetime import datetime, timezone

import anthropic
import openai

import config
import db
from scoring import aggregate_run_scores, compute_composite_scores
from regression_detector import detect_regressions
from outage_monitor import preflight_check

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# API call abstraction
# ---------------------------------------------------------------------------

def call_model(
    model_config: dict,
    prompt: str,
    system_prompt: str | None = None,
) -> tuple[str | None, int | None, int | None, int | None, str | None]:
    """
    Call a model's API and return (response_text, latency_ms, prompt_tokens, completion_tokens, error).

    On success, error is None.
    On failure, response_text is None and error contains the message.
    """
    provider = model_config["provider"]
    api_model = model_config["api_model"]
    extra_params = model_config.get("extra_params", {})

    start_time = time.monotonic()

    try:
        if provider == "anthropic":
            return _call_anthropic(api_model, prompt, system_prompt, extra_params)
        elif provider in ("openai", "xai"):
            base_url = model_config.get("base_url")
            api_key = config.XAI_API_KEY if provider == "xai" else config.OPENAI_API_KEY
            return _call_openai(api_model, prompt, system_prompt, extra_params, base_url, api_key)
        else:
            return (None, None, None, None, f"Unknown provider: {provider}")
    except Exception as e:
        elapsed = int((time.monotonic() - start_time) * 1000)
        error_msg = f"{type(e).__name__}: {e}"
        logger.error("API call failed for %s: %s", model_config["id"], error_msg)
        return (None, elapsed, None, None, error_msg)


def _call_anthropic(
    model: str,
    prompt: str,
    system_prompt: str | None,
    extra_params: dict,
) -> tuple[str | None, int, int | None, int | None, str | None]:
    """Call the Anthropic API."""
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY, timeout=120.0)

    kwargs = {
        "model": model,
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system_prompt:
        kwargs["system"] = system_prompt
    kwargs.update(extra_params)

    start = time.monotonic()
    response = client.messages.create(**kwargs)
    elapsed = int((time.monotonic() - start) * 1000)

    text = ""
    for block in response.content:
        if hasattr(block, "text"):
            text += block.text

    prompt_tokens = response.usage.input_tokens if response.usage else None
    completion_tokens = response.usage.output_tokens if response.usage else None

    return (text, elapsed, prompt_tokens, completion_tokens, None)


def _call_openai(
    model: str,
    prompt: str,
    system_prompt: str | None,
    extra_params: dict,
    base_url: str | None,
    api_key: str,
) -> tuple[str | None, int, int | None, int | None, str | None]:
    """Call the OpenAI-compatible API (also used for xAI/Grok)."""
    client_kwargs = {"api_key": api_key, "timeout": 120.0}
    if base_url:
        client_kwargs["base_url"] = base_url

    client = openai.OpenAI(**client_kwargs)

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    kwargs = {
        "model": model,
        "messages": messages,
        "max_tokens": 4096,
    }
    # Handle reasoning_effort for o3
    if "reasoning_effort" in extra_params:
        kwargs["reasoning_effort"] = extra_params["reasoning_effort"]

    start = time.monotonic()
    response = client.chat.completions.create(**kwargs)
    elapsed = int((time.monotonic() - start) * 1000)

    text = response.choices[0].message.content if response.choices else ""
    prompt_tokens = response.usage.prompt_tokens if response.usage else None
    completion_tokens = response.usage.completion_tokens if response.usage else None

    return (text, elapsed, prompt_tokens, completion_tokens, None)


# ---------------------------------------------------------------------------
# Evaluation stub
# ---------------------------------------------------------------------------

def evaluate_response(test_config: dict, model_output: str) -> tuple[float, dict]:
    """
    Evaluate a model's output for a test.

    Returns (score, eval_details).

    NOTE: This is a placeholder. In production, this would run the appropriate
    evaluator (sandbox_exec, llm_judge, exact_match) based on test_config["eval_type"].
    For now, it returns a score based on output length and basic checks.
    """
    if not model_output or len(model_output.strip()) < 10:
        return (0.0, {"reason": "empty_or_too_short"})

    # Placeholder scoring - in production, this dispatches to real evaluators
    # The actual evaluation infrastructure lives in benchmark/tests/
    eval_type = test_config.get("eval_type", "llm_judge")
    details = {
        "eval_type": eval_type,
        "output_length": len(model_output),
        "placeholder": True,
    }

    # Base score on response characteristics (placeholder logic)
    base_score = min(95.0, 60.0 + len(model_output) / 100)
    return (round(base_score, 1), details)


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def run_benchmarks(schedule: str) -> None:
    """Execute a full benchmark run."""
    logger.info("Starting benchmark run (schedule=%s)", schedule)

    # 1. Initialize database
    conn = db.init_db()
    db.seed_models_and_categories(conn)

    # 2. Pre-flight outage check
    logger.info("Running outage pre-flight check...")
    outage_results = preflight_check(conn)
    for model_id, is_up in outage_results.items():
        if not is_up:
            logger.warning("Model %s failed pre-flight check", model_id)

    # 3. Create benchmark run
    run_id = db.create_run(conn, schedule)
    logger.info("Created benchmark run: %s", run_id)

    # 4. Get active models and tests
    active_models = db.get_active_models(conn)
    active_tests = db.get_active_tests(conn)

    total_tests = 0
    passed_tests = 0
    errors = []

    # 5. Run tests
    for model_row in active_models:
        model_id = model_row["id"]
        model_cfg = config.get_model_by_id(model_id)
        if not model_cfg:
            logger.error("No config found for model %s", model_id)
            continue

        # Skip if model is in outage
        open_outage = db.get_open_outage(conn, model_id)
        if open_outage and open_outage["check_count"] >= 3:
            logger.warning("Skipping model %s (in outage since %s)", model_id, open_outage["started_at"])
            continue

        logger.info("Testing model: %s (%s)", model_cfg["name"], model_cfg["api_model"])

        for test_row in active_tests:
            test_id = test_row["id"]
            category_id = test_row["category_id"]
            total_tests += 1

            try:
                # Build the prompt
                test_prompt = test_row.get("prompt") or test_row["description"]
                system_prompt = (
                    "You are being evaluated on a coding/reasoning benchmark. "
                    "Provide thorough, correct, and well-structured responses."
                )

                # Call the model
                response_text, latency_ms, prompt_tokens, completion_tokens, error = call_model(
                    model_cfg, test_prompt, system_prompt
                )

                if error:
                    # API error
                    db.save_test_result(
                        conn, run_id, model_id, test_id, category_id,
                        score=None, raw_score=None, latency_ms=latency_ms,
                        token_count=None, prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        model_output=None, eval_details=None, error=error,
                    )
                    errors.append(f"{model_id}/{test_id}: {error}")
                    logger.error("Test failed: %s/%s - %s", model_id, test_id, error)
                else:
                    # Evaluate the response
                    score, eval_details = evaluate_response(test_row, response_text)
                    token_count = (prompt_tokens or 0) + (completion_tokens or 0)

                    db.save_test_result(
                        conn, run_id, model_id, test_id, category_id,
                        score=score, raw_score=score, latency_ms=latency_ms,
                        token_count=token_count, prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        model_output=response_text, eval_details=eval_details,
                        error=None,
                    )
                    passed_tests += 1
                    logger.info("  %s/%s: score=%.1f latency=%dms",
                                model_id, test_id, score, latency_ms or 0)

            except Exception as e:
                error_msg = f"{type(e).__name__}: {e}"
                errors.append(f"{model_id}/{test_id}: {error_msg}")
                logger.error("Unexpected error for %s/%s: %s", model_id, test_id, error_msg)
                logger.debug(traceback.format_exc())

                db.save_test_result(
                    conn, run_id, model_id, test_id, category_id,
                    score=None, raw_score=None, latency_ms=None,
                    token_count=None, prompt_tokens=None, completion_tokens=None,
                    model_output=None, eval_details=None, error=error_msg,
                )

    # 6. Aggregate scores
    logger.info("Aggregating scores...")
    aggregate_run_scores(conn, run_id)

    # 7. Compute composite scores and ranks
    logger.info("Computing composite scores...")
    compute_composite_scores(conn, run_id)

    # 8. Regression detection
    logger.info("Running regression detection...")
    detect_regressions(conn, run_id)

    # 9. Complete the run
    error_log = "\n".join(errors) if errors else None
    db.complete_run(conn, run_id, total_tests, passed_tests, error_log)

    logger.info(
        "Benchmark run complete: %d/%d tests passed (%d errors)",
        passed_tests, total_tests, len(errors),
    )

    conn.close()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Run ModelRegression benchmarks")
    parser.add_argument(
        "--schedule",
        choices=["morning", "afternoon", "night"],
        default="night",
        help="Schedule label for this run (default: night)",
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
        run_benchmarks(args.schedule)
    except Exception as e:
        logger.critical("Benchmark run failed: %s", e)
        logger.debug(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
