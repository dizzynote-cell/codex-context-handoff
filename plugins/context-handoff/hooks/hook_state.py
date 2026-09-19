"""Small, dependency-free state helper shared by plugin hooks."""

from __future__ import annotations

import json
import os
import re
import tempfile
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


def session_key(value: Any) -> str:
    text = str(value or "unknown-session")
    return re.sub(r"[^A-Za-z0-9._-]", "_", text)[:160]


def state_path(session_id: Any) -> Path:
    directory = plugin_data_dir() / "sessions"
    directory.mkdir(parents=True, exist_ok=True)
    return directory / f"{session_key(session_id)}.json"


def load_state(session_id: Any) -> dict[str, Any]:
    path = state_path(session_id)
    if not path.exists():
        return {"session_id": str(session_id or ""), "compaction_count": 0, "compact_turn_ids": []}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {"session_id": str(session_id or ""), "compaction_count": 0, "compact_turn_ids": []}


def save_state(session_id: Any, state: dict[str, Any]) -> None:
    path = state_path(session_id)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, path)
