from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HOOKS = Path(__file__).resolve().parents[1] / "hooks"
sys.path.insert(0, str(HOOKS))

from hook_state import inspect_transcript, save_bootstrap_state  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Backfill compaction counts for recently active local Codex sessions."
    )
    parser.add_argument(
        "--sessions-root",
        type=Path,
        default=Path.home() / ".codex" / "sessions",
    )
    parser.add_argument("--active-days", type=int, default=14)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    if args.active_days < 1:
        parser.error("--active-days must be positive")
    if not args.sessions_root.is_dir():
        print(json.dumps({"error": "sessions root is unavailable or not readable"}, ensure_ascii=False))
        return 1

    cutoff = time.time() - args.active_days * 86400
    results: list[dict[str, object]] = []
    failures: list[dict[str, str]] = []
    for transcript in sorted(args.sessions_root.rglob("*.jsonl"), key=lambda path: path.stat().st_mtime):
        try:
            if transcript.stat().st_mtime < cutoff:
                continue
            inspected = inspect_transcript(transcript)
            session_id = str(inspected.get("session_id") or "")
            if not session_id:
                raise ValueError("session id is missing")
            count = int(inspected.get("compaction_count") or 0)
            if count == 0:
                continue
            record = {
                "session_id": session_id,
                "compaction_count": count,
                "eligible": count >= 4,
                "cwd": str(inspected.get("cwd") or ""),
                "backfilled_at": datetime.now(timezone.utc).isoformat(),
                "count_source": "transcript_backfill",
                "compact_turn_ids": [],
            }
            if args.apply:
                save_bootstrap_state(session_id, record)
            results.append({
                "session_id": session_id,
                "compaction_count": count,
                "eligible": count >= 4,
                "cwd": record["cwd"],
            })
        except (OSError, ValueError) as error:
            failures.append({"file": transcript.name, "error": str(error)})

    print(json.dumps({
        "applied": args.apply,
        "active_days": args.active_days,
        "initialized": results,
        "failures": failures,
    }, ensure_ascii=False, indent=2))
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
