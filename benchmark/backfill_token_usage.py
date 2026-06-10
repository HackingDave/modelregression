#!/usr/bin/env python3
"""
Backfill missing token usage for benchmark rows from local CLI session artifacts.

Codex usage is recovered from persisted rollout files in ~/.codex.
Grok usage is recovered from session updates in ~/.grok.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

BENCHMARK_DIR = Path(__file__).resolve().parent
if str(BENCHMARK_DIR) not in sys.path:
    sys.path.insert(0, str(BENCHMARK_DIR))

import config
import db
import runner

BENCHMARK_CWD = str(BENCHMARK_DIR)


@dataclass
class UsageEntry:
    key: str
    prompt: str
    created_at: datetime
    total_tokens: int
    prompt_tokens: int | None
    completion_tokens: int | None


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backfill benchmark token usage")
    parser.add_argument("--db", default=config.DB_PATH, help="Path to benchmarks.db")
    parser.add_argument("--dry-run", action="store_true", help="Print matches without updating the database")
    return parser.parse_args()


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _extract_codex_prompt(text: str) -> str:
    marker = "\n\n---\n\n"
    if marker in text:
        return text.split(marker, 1)[1].strip()
    return text.strip()


def _iter_codex_entries() -> Iterable[UsageEntry]:
    db_path = os.path.expanduser("~/.codex/state_5.sqlite")
    if not os.path.exists(db_path):
        return []

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """SELECT id, created_at_ms, created_at, first_user_message
               FROM threads
               WHERE cwd = ? AND model = ?
               ORDER BY created_at_ms ASC""",
            (BENCHMARK_CWD, "gpt-5.5"),
        ).fetchall()
    finally:
        conn.close()

    entries = []
    for row in rows:
        prompt = _extract_codex_prompt(row["first_user_message"] or "")
        prompt_tokens, completion_tokens, total_tokens = runner._read_codex_usage_from_thread(row["id"])
        if not prompt or total_tokens is None:
            continue

        created_at_ms = row["created_at_ms"] or (row["created_at"] * 1000)
        created_at = datetime.fromtimestamp(created_at_ms / 1000, tz=timezone.utc)
        entries.append(
            UsageEntry(
                key=row["id"],
                prompt=prompt,
                created_at=created_at,
                total_tokens=total_tokens,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            )
        )
    return entries


def _iter_grok_entries() -> Iterable[UsageEntry]:
    session_root = Path(os.path.expanduser("~/.grok/sessions")) / runner.quote(BENCHMARK_CWD, safe="")
    if not session_root.exists():
        return []

    entries = []
    for session_dir in sorted(path for path in session_root.iterdir() if path.is_dir()):
        summary_path = session_dir / "summary.json"
        chat_path = session_dir / "chat_history.jsonl"
        if not summary_path.exists() or not chat_path.exists():
            continue

        summary = json.loads(summary_path.read_text())
        request_id = summary.get("request_id")
        total_tokens = runner._read_grok_usage_from_session(session_dir.name, request_id, BENCHMARK_CWD)
        if total_tokens is None:
            continue

        prompt = ""
        for line in chat_path.read_text().splitlines():
            entry = json.loads(line)
            if entry.get("type") != "user":
                continue
            for content in entry.get("content", []):
                text = content.get("text", "")
                if "<user_query>" in text:
                    prompt = runner._extract_user_query(text)
                    break
            if prompt:
                break

        if not prompt:
            continue

        entries.append(
            UsageEntry(
                key=session_dir.name,
                prompt=prompt,
                created_at=_parse_iso(summary["created_at"]),
                total_tokens=total_tokens,
                prompt_tokens=None,
                completion_tokens=None,
            )
        )
    return entries


def _build_prompt_map() -> dict[str, str]:
    return {
        test.id: test.prompt
        for test in runner.TEST_REGISTRY.values()
    }


def _pick_candidate(
    candidates: list[UsageEntry],
    run_started_at: datetime,
    used_keys: set[str],
) -> UsageEntry | None:
    available = [entry for entry in candidates if entry.key not in used_keys]
    if not available:
        return None

    available.sort(
        key=lambda entry: (
            abs((entry.created_at - run_started_at).total_seconds()),
            entry.created_at,
        )
    )
    return available[0]


def main() -> int:
    args = _parse_args()
    conn = db.get_connection(args.db)
    prompt_map = _build_prompt_map()

    usage_index: dict[str, dict[str, list[UsageEntry]]] = {
        "gpt-5-5": {},
        "grok": {},
    }

    for entry in _iter_codex_entries():
        usage_index["gpt-5-5"].setdefault(entry.prompt, []).append(entry)
    for entry in _iter_grok_entries():
        usage_index["grok"].setdefault(entry.prompt, []).append(entry)

    rows = conn.execute(
        """SELECT tr.id, tr.run_id, tr.model_id, tr.test_id, br.started_at
           FROM test_results tr
           JOIN benchmark_runs br ON br.id = tr.run_id
           WHERE tr.model_id IN ('gpt-5-5', 'grok')
             AND tr.error IS NULL
             AND tr.token_count IS NULL
           ORDER BY br.started_at ASC""",
    ).fetchall()

    used_keys: set[str] = set()
    updates: list[tuple[int, int | None, int | None, str]] = []
    unmatched: list[tuple[str, str, str]] = []

    for row in rows:
        prompt = prompt_map.get(row["test_id"])
        if not prompt:
            unmatched.append((row["model_id"], row["test_id"], "missing prompt"))
            continue

        candidates = usage_index.get(row["model_id"], {}).get(prompt, [])
        candidate = _pick_candidate(candidates, _parse_iso(row["started_at"]), used_keys)
        if not candidate:
            unmatched.append((row["model_id"], row["test_id"], "no matching session"))
            continue

        used_keys.add(candidate.key)
        updates.append(
            (
                candidate.total_tokens,
                candidate.prompt_tokens,
                candidate.completion_tokens,
                row["id"],
            )
        )

    if args.dry_run:
        print(f"Matched {len(updates)} rows")
        for total_tokens, prompt_tokens, completion_tokens, row_id in updates[:10]:
            print(row_id, total_tokens, prompt_tokens, completion_tokens)
    else:
        conn.executemany(
            """UPDATE test_results
               SET token_count = ?, prompt_tokens = ?, completion_tokens = ?
               WHERE id = ?""",
            updates,
        )
        conn.commit()
        print(f"Updated {len(updates)} rows")

    if unmatched:
        print(f"Unmatched rows: {len(unmatched)}")
        for model_id, test_id, reason in unmatched[:10]:
            print(model_id, test_id, reason)

    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
