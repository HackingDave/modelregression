"""
Outage monitor for AI model APIs.

Can be run standalone or imported by the runner for pre-flight checks.
Sends a simple health-check prompt to each model and tracks consecutive failures.
"""

import argparse
import logging
import time
import traceback

import anthropic
import openai

import config
import db as database

logger = logging.getLogger(__name__)

HEALTH_CHECK_PROMPT = "Hello, respond with just 'OK'"
HEALTH_CHECK_TIMEOUT = 30  # seconds
FAILURE_THRESHOLD = 3  # consecutive failures before declaring outage


def _check_model(model_cfg: dict) -> tuple[bool, str | None, int | None]:
    """
    Send a health-check prompt to a model.

    Returns (is_healthy, error_message, http_status).
    """
    provider = model_cfg["provider"]
    api_model = model_cfg["api_model"]

    try:
        if provider == "anthropic":
            client = anthropic.Anthropic(
                api_key=config.ANTHROPIC_API_KEY,
                timeout=HEALTH_CHECK_TIMEOUT,
            )
            response = client.messages.create(
                model=api_model,
                max_tokens=10,
                messages=[{"role": "user", "content": HEALTH_CHECK_PROMPT}],
            )
            text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    text += block.text
            if text.strip():
                return (True, None, None)
            else:
                return (False, "Empty response", None)

        elif provider in ("openai", "xai"):
            client_kwargs = {"timeout": HEALTH_CHECK_TIMEOUT}
            if provider == "xai":
                client_kwargs["api_key"] = config.XAI_API_KEY
                client_kwargs["base_url"] = model_cfg.get("base_url", "https://api.x.ai/v1")
            else:
                client_kwargs["api_key"] = config.OPENAI_API_KEY

            client = openai.OpenAI(**client_kwargs)
            response = client.chat.completions.create(
                model=api_model,
                max_tokens=10,
                messages=[{"role": "user", "content": HEALTH_CHECK_PROMPT}],
            )
            text = response.choices[0].message.content if response.choices else ""
            if text.strip():
                return (True, None, None)
            else:
                return (False, "Empty response", None)

        else:
            return (False, f"Unknown provider: {provider}", None)

    except anthropic.APIStatusError as e:
        return (False, str(e.message), e.status_code)
    except openai.APIStatusError as e:
        return (False, str(e.message), e.status_code)
    except anthropic.APITimeoutError:
        return (False, "Request timed out", None)
    except openai.APITimeoutError:
        return (False, "Request timed out", None)
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
        logger.info("Health check: %s (%s)", model_cfg["name"], model_cfg["api_model"])

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
                provider=model_cfg["provider"],
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
