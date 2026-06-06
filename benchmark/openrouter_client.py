"""
Small stdlib OpenRouter client for benchmark calls and model discovery.

OpenRouter exposes an OpenAI-compatible chat-completions endpoint and a model
catalog endpoint. Keeping this dependency-free preserves the current benchmark
engine deployment model.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


API_BASE = os.getenv("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1")
DEFAULT_REFERER = "https://modelregression.com"
DEFAULT_TITLE = "ModelRegression.com"


def _headers(include_auth: bool = True) -> dict[str, str]:
    headers = {
        "Content-Type": "application/json",
        "HTTP-Referer": os.getenv("OPENROUTER_HTTP_REFERER", DEFAULT_REFERER),
        "X-Title": os.getenv("OPENROUTER_APP_TITLE", DEFAULT_TITLE),
        "User-Agent": "modelregression-benchmark/1.0",
    }
    api_key = os.getenv("OPENROUTER_API_KEY")
    if include_auth and api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def fetch_models_catalog(timeout: int = 30) -> list[dict[str, Any]]:
    """Return OpenRouter's current model catalog."""
    query = urllib.parse.urlencode({"output_modalities": "text"})
    url = f"{API_BASE.rstrip('/')}/models?{query}"
    request = urllib.request.Request(url, headers=_headers(include_auth=True))
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return list(payload.get("data") or [])


def _content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text" and isinstance(item.get("text"), str):
                    parts.append(item["text"])
                elif isinstance(item.get("content"), str):
                    parts.append(item["content"])
            elif isinstance(item, str):
                parts.append(item)
        return "\n".join(parts)
    return "" if content is None else str(content)


def call_chat_completion(
    model_id: str,
    prompt: str,
    system_prompt: str | None = None,
    timeout: int = 300,
    supported_parameters: list[str] | None = None,
) -> tuple[str | None, int | None, int | None, int | None, str | None, int | None]:
    """
    Call OpenRouter chat completions.

    Returns (text, latency_ms, prompt_tokens, completion_tokens, error, http_status).
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return (None, None, None, None, "OPENROUTER_API_KEY is not set", None)

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    body = {
        "model": model_id,
        "messages": messages,
    }
    supported = set(supported_parameters or [])
    if supported_parameters is None or "temperature" in supported:
        body["temperature"] = float(os.getenv("OPENROUTER_TEMPERATURE", "0"))
    if supported_parameters is None or "max_tokens" in supported:
        body["max_tokens"] = int(os.getenv("OPENROUTER_MAX_TOKENS", "4096"))

    url = f"{API_BASE.rstrip('/')}/chat/completions"
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers=_headers(include_auth=True),
        method="POST",
    )

    start = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            elapsed = int((time.monotonic() - start) * 1000)
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        elapsed = int((time.monotonic() - start) * 1000)
        try:
            err_body = e.read().decode("utf-8")[:600]
        except Exception:
            err_body = e.reason or "HTTP error"
        return (None, elapsed, None, None, f"OpenRouter HTTP {e.code}: {err_body}", e.code)
    except urllib.error.URLError as e:
        elapsed = int((time.monotonic() - start) * 1000)
        return (None, elapsed, None, None, f"OpenRouter URL error: {e.reason}", None)
    except TimeoutError:
        return (None, timeout * 1000, None, None, "OpenRouter request timed out", None)
    except Exception as e:
        elapsed = int((time.monotonic() - start) * 1000)
        return (None, elapsed, None, None, f"{type(e).__name__}: {e}", None)

    choices = payload.get("choices") or []
    if not choices:
        return (None, elapsed, None, None, "OpenRouter returned no choices", None)

    message = choices[0].get("message") or {}
    text = _content_to_text(message.get("content")).strip()
    if not text:
        return (None, elapsed, None, None, "Empty response from OpenRouter", None)

    usage = payload.get("usage") or {}
    return (
        text,
        elapsed,
        usage.get("prompt_tokens"),
        usage.get("completion_tokens"),
        None,
        None,
    )
