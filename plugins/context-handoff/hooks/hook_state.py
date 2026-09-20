"""Small, dependency-free state helper shared by plugin hooks."""

from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def plugin_data_dir() -> Path:
    configured = os.environ.get("PLUGIN_DATA") or os.environ.get("CLAUDE_PLUGIN_DATA")
    if configured:
        root = Path(configured)
    else:
        root = Path(tempfile.gettempdir()) / "context-handoff-plugin-data"
    root.mkdir(parents=True, exist_ok=True)
    return root


def bootstrap_data_dir() -> Path:
    configured = os.environ.get("CONTEXT_HANDOFF_BOOTSTRAP_DATA")
    root = Path(configured) if configured else Path.home() / ".codex" / "state" / "context-handoff-bootstrap"
    root.mkdir(parents=True, exist_ok=True)
    return root


def session_key(value: Any) -> str:
    text = str(value or "unknown-session")
    return re.sub(r"[^A-Za-z0-9._-]", "_", text)[:160]


def state_path(session_id: Any) -> Path:
    directory = plugin_data_dir() / "sessions"
    directory.mkdir(parents=True, exist_ok=True)
    return directory / f"{session_key(session_id)}.json"


def bootstrap_state_path(session_id: Any) -> Path:
    directory = bootstrap_data_dir() / "sessions"
    directory.mkdir(parents=True, exist_ok=True)
    return directory / f"{session_key(session_id)}.json"


def default_state(session_id: Any) -> dict[str, Any]:
    return {"session_id": str(session_id or ""), "compaction_count": 0, "compact_turn_ids": []}


def read_json_state(path: Path, session_id: Any) -> dict[str, Any]:
    if not path.exists():
        return default_state(session_id)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else default_state(session_id)
    except (OSError, json.JSONDecodeError):
        return default_state(session_id)


def load_state(session_id: Any) -> dict[str, Any]:
    state = read_json_state(state_path(session_id), session_id)
    bootstrap = read_json_state(bootstrap_state_path(session_id), session_id)
    current = int(state.get("compaction_count") or 0)
    imported = int(bootstrap.get("compaction_count") or 0)
    if imported > current:
        state["compaction_count"] = imported
        state["eligible"] = imported >= 4
        state["backfilled_at"] = bootstrap.get("backfilled_at")
        state["count_source"] = "transcript_backfill"
        state["cwd"] = str(state.get("cwd") or bootstrap.get("cwd") or "")
    return state


def save_state(session_id: Any, state: dict[str, Any]) -> None:
    path = state_path(session_id)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, path)


def save_bootstrap_state(session_id: Any, state: dict[str, Any]) -> None:
    path = bootstrap_state_path(session_id)
    existing = read_json_state(path, session_id)
    if int(existing.get("compaction_count") or 0) > int(state.get("compaction_count") or 0):
        state = existing
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, path)


def inspect_transcript(transcript_path: object) -> dict[str, Any]:
    if not transcript_path:
        raise ValueError("host did not provide a transcript path")
    path = Path(str(transcript_path))
    if not path.is_file():
        raise ValueError("transcript is unavailable or not readable")

    count = 0
    parsed_events = 0
    session_id = ""
    cwd = ""
    try:
        with path.open(encoding="utf-8-sig") as handle:
            for line in handle:
                try:
                    event = json.loads(line)
                except (json.JSONDecodeError, TypeError):
                    continue
                if not isinstance(event, dict):
                    continue
                parsed_events += 1
                payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
                item = event.get("item") if isinstance(event.get("item"), dict) else {}
                if "compacted" in {event.get("type"), payload.get("type"), item.get("type")}:
                    count += 1
                if event.get("type") == "session_meta":
                    session_id = str(payload.get("id") or session_id)
                    cwd = str(payload.get("cwd") or cwd)
    except (OSError, UnicodeError) as error:
        raise ValueError("transcript is unavailable or not readable") from error

    if parsed_events == 0:
        raise ValueError("transcript format is not recognized")
    return {"session_id": session_id, "cwd": cwd, "compaction_count": count, "path": str(path)}


def backfill_current_session(session_id: Any, transcript_path: object, cwd: object = "") -> dict[str, Any]:
    inspected = inspect_transcript(transcript_path)
    transcript_session = inspected.get("session_id")
    if transcript_session and str(session_id) != transcript_session:
        raise ValueError("transcript does not belong to the current session")

    state = load_state(session_id)
    observed = int(inspected["compaction_count"])
    state["compaction_count"] = max(int(state.get("compaction_count") or 0), observed)
    state["eligible"] = state["compaction_count"] >= 4
    state["cwd"] = str(cwd or state.get("cwd") or inspected.get("cwd") or "")
    state["backfilled_at"] = datetime.now(timezone.utc).isoformat()
    state["count_source"] = "transcript_backfill"
    save_state(session_id, state)
    return state
