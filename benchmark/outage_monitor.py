"""
Outage monitor for AI model CLI tools.

Can be run standalone or imported by the runner for pre-flight checks.
Sends a simple health-check prompt to each model via its CLI tool and
tracks consecutive failures.
"""

import argparse
import logging
import os
import signal
import subprocess
import time
import traceback

import config
import db as database

logger = logging.getLogger(__name__)

HEALTH_CHECK_PROMPT = "Respond with just the word OK"
FAILURE_THRESHOLD = 3


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


def _check_model(model_cfg: dict) -> tuple[bool, str | None, int | None]:
    """
    Send a health-check prompt to a model via its CLI tool.

    Returns (is_healthy, error_message, http_status).
    http_status is always None for CLI-based checks.
    """
    cli = model_cfg["cli"]
    cli_model = model_cfg["cli_model"]

    try:
        if cli == "claude":
            cmd = ["claude", "-p", "--model", cli_model]
            result = _run_cli(cmd, input=HEALTH_CHECK_PROMPT, timeout=config.HEALTH_CHECK_TIMEOUT)
        elif cli == "codex":
            cmd = ["codex", "exec", "-m", cli_model, "--sandbox", "read-only"]
            result = _run_cli(cmd, input=HEALTH_CHECK_PROMPT, timeout=config.HEALTH_CHECK_TIMEOUT)
        elif cli == "gemini":
            cmd = ["gemini", "-p", HEALTH_CHECK_PROMPT, "-m", cli_model]
            result = _run_cli(cmd, timeout=config.HEALTH_CHECK_TIMEOUT)
        elif cli == "agent":
            cmd = ["agent", "-p", HEALTH_CHECK_PROMPT, "-m", cli_model, "--output-format", "plain"]
            result = _run_cli(cmd, timeout=config.HEALTH_CHECK_TIMEOUT)
        else:
            return (False, f"Unknown CLI tool: {cli}", None)

        if result.returncode != 0:
            stderr = result.stderr.strip()[:300] if result.stderr else "unknown error"
            return (False, f"{cli} exited {result.returncode}: {stderr}", None)

        text = result.stdout.strip()
        if text:
            return (True, None, None)
        else:
            return (False, "Empty response", None)

    except subprocess.TimeoutExpired:
        return (False, "Request timed out", None)
    except FileNotFoundError:
        return (False, f"CLI tool '{cli}' not found", None)
    except Exception as e:
        return (False, f"{type(e).__name__}: {e}", None)


def check_all_models(conn) -> dict[str, bool]:
    """
    Check all active models and update outage records.

    Returns a dict mapping model_id -> is_healthy.
    """
    results = {}

    for model_cfg in config.MODELS:
        if not model_cfg["is_active"]:
            continue

        model_id = model_cfg["id"]
        logger.info("Health check: %s (%s via %s)", model_cfg["name"], model_cfg["cli_model"], model_cfg["cli"])

        is_healthy, error_msg, http_status = _check_model(model_cfg)

        if is_healthy:
            logger.info("  %s: healthy", model_id)
            # Check if there's an open outage to resolve
            open_outage = database.get_open_outage(conn, model_id)
            if open_outage:
                database.resolve_outage(conn, model_id)
                logger.info("  Outage resolved for %s", model_id)
            results[model_id] = True
        else:
            logger.warning("  %s: UNHEALTHY - %s (HTTP %s)", model_id, error_msg, http_status)

            # Determine error_type
            error_type = str(http_status) if http_status else "timeout" if "timed out" in (error_msg or "") else "error"

            database.create_or_update_outage(
                conn,
                provider=model_cfg["cli"],
                model_id=model_id,
                error_type=error_type,
                error_message=error_msg or "Unknown error",
                http_status=http_status,
            )

            # Check if we've reached the failure threshold
            outage = database.get_open_outage(conn, model_id)
            if outage and outage["check_count"] >= FAILURE_THRESHOLD:
                logger.error("  %s: OUTAGE CONFIRMED (%d consecutive failures)",
                             model_id, outage["check_count"])

            results[model_id] = False

    return results


def preflight_check(conn) -> dict[str, bool]:
    """
    Quick pre-flight check before a benchmark run.
    Same as check_all_models but logged differently.
    """
    logger.info("Running outage pre-flight check...")
    results = check_all_models(conn)

    healthy = sum(1 for v in results.values() if v)
    total = len(results)
    logger.info("Pre-flight: %d/%d models healthy", healthy, total)

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Check AI model API health")
    parser.add_argument("--verbose", "-v", action="store_true", help="Debug logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    conn = database.init_db()
    database.seed_models_and_categories(conn)

    results = check_all_models(conn)

    print("\n=== Outage Monitor Results ===")
    for model_id, healthy in results.items():
        status = "OK" if healthy else "DOWN"
        print(f"  {model_id}: {status}")

    conn.close()


if __name__ == "__main__":
    main()
