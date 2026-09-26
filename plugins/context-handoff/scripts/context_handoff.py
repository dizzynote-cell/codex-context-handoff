"""Idempotent handoff transaction and portable new-task adapters."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import tomllib
except ImportError:  # pragma: no cover - Python < 3.11
    tomllib = None


DEFAULT_BRIDGE_URL = "http://127.0.0.1:8765/api/local-tasks"
ACTIVE_STATUSES = {"preparing", "ready", "dispatching", "dispatched"}
CONTINUATION_PREFIX = re.compile(r"^\s*继续开发\s*(\d+)(?=$|[\s｜|·:：—-])")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_key(value: str) -> str:
    return "".join(c if c.isalnum() or c in "._-" else "_" for c in value)[:160]


def data_root() -> Path:
    configured = os.environ.get("PLUGIN_DATA") or os.environ.get("CLAUDE_PLUGIN_DATA")
    root = Path(configured) if configured else Path.home() / ".codex" / "context-handoff-data"
    root.mkdir(parents=True, exist_ok=True)
    return root


def session_id(value: str | None, cwd: Path) -> str:
    return value or f"manual-{hashlib.sha256(str(cwd).encode()).hexdigest()[:16]}"


def session_record_path(sid: str) -> Path:
    path = data_root() / "transactions"
    path.mkdir(parents=True, exist_ok=True)
    return path / f"{safe_key(sid)}.json"


def read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {} if default is None else default


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, path)


def compact_count(sid: str) -> int:
    path = data_root() / "sessions" / f"{safe_key(sid)}.json"
    return int(read_json(path, {}).get("compaction_count") or 0)


def begin(args: argparse.Namespace) -> dict[str, Any]:
    cwd = Path(args.cwd).resolve()
    sid = session_id(args.session_id, cwd)
    record_path = session_record_path(sid)
    record = read_json(record_path, {})
    current = record.get("current") if isinstance(record, dict) else None
    if isinstance(current, dict) and current.get("status") in ACTIVE_STATUSES:
        return {"ok": True, "reused": True, **current}

    sequence = int(record.get("last_sequence") or 0) + 1
    chain_id = str(record.get("chain_id") or f"{cwd.name}-{hashlib.sha256((sid + str(cwd)).encode()).hexdigest()[:10]}")
    handoff_dir = cwd / ".codex" / "handoffs" / chain_id
    handoff_dir.mkdir(parents=True, exist_ok=True)
    stamp = f"{sequence:03d}"
    transaction = {
        "status": "preparing",
        "session_id": sid,
        "chain_id": chain_id,
        "sequence": sequence,
        "mode": args.mode,
        "cwd": str(cwd),
        "created_at": now(),
        "compaction_count": compact_count(sid),
        "handoff_path": str(handoff_dir / f"HANDOFF_{stamp}.md"),
        "prompt_path": str(handoff_dir / f"START_PROMPT_{stamp}.md"),
        "state_path": str(handoff_dir / f"STATE_{stamp}.json"),
    }
    record = {"session_id": sid, "chain_id": chain_id, "last_sequence": sequence, "current": transaction}
    atomic_json(record_path, record)
    atomic_json(Path(transaction["state_path"]), transaction)
    return {"ok": True, "reused": False, **transaction}


def current_transaction(args: argparse.Namespace) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    cwd = Path(args.cwd).resolve()
    sid = session_id(args.session_id, cwd)
    path = session_record_path(sid)
    record = read_json(path, {})
    transaction = record.get("current") if isinstance(record, dict) else None
    if not isinstance(transaction, dict):
        raise RuntimeError("No handoff transaction exists. Run begin first.")
    return path, record, transaction


def continuation_title(source_title: str, proposed_title: str) -> str:
    """Number a continuation from its source title, never from handoff file sequence."""
    title = proposed_title.strip()
    if not title:
        raise RuntimeError("Title must not be empty")
    source = CONTINUATION_PREFIX.match(source_title or "")
    proposed = CONTINUATION_PREFIX.match(title)
    if not source:
        if proposed:
            raise RuntimeError("A numbered continuation requires the source task title")
        return title
    stage = title[proposed.end():].strip(" ｜|·:：—-\t") if proposed else title
    if not stage:
        stage = source_title[source.end():].strip(" ｜|·:：—-\t")
    number = int(source.group(1)) + 1
    return f"继续开发 {number}｜{stage}" if stage else f"继续开发 {number}"


def finalize(args: argparse.Namespace) -> dict[str, Any]:
    path, record, tx = current_transaction(args)
    if tx.get("status") == "dispatched":
        return {"ok": True, "reused": True, **tx}
    handoff = Path(tx["handoff_path"])
    prompt = Path(tx["prompt_path"])
    if not handoff.is_file() or handoff.stat().st_size < 80:
        raise RuntimeError(f"Handoff document is missing or too short: {handoff}")
    if not prompt.is_file() or prompt.stat().st_size < 40:
        raise RuntimeError(f"Startup prompt is missing or too short: {prompt}")
    source_title = str(args.source_title or tx.get("source_title") or "").strip()
    title = continuation_title(source_title, args.title) if tx.get("mode") == "continuation" else args.title.strip()
    if not title:
        raise RuntimeError("Title must not be empty")
    tx.update({"status": "ready", "title": title, "source_title": source_title, "ready_at": now()})
    record["current"] = tx
    atomic_json(path, record)
    atomic_json(Path(tx["state_path"]), tx)
    return {"ok": True, "reused": False, **tx}


def load_config(cwd: Path) -> tuple[dict[str, Any], str | None]:
    candidates = []
    if os.environ.get("CONTEXT_HANDOFF_CONFIG"):
        candidates.append(Path(os.environ["CONTEXT_HANDOFF_CONFIG"]))
    candidates.extend([cwd / ".codex" / "context-handoff.toml", Path.home() / ".codex" / "context-handoff.toml"])
    for path in candidates:
        if path.is_file():
            if tomllib is None:
                raise RuntimeError("TOML configuration requires Python 3.11 or newer")
            with path.open("rb") as handle:
                return tomllib.load(handle), str(path)
    return {}, None


def endpoint_reachable(url: str, timeout: float = 0.25) -> bool:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return False
    try:
        with socket.create_connection((parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80)), timeout):
            return True
    except OSError:
        return False


def post_json(url: str, payload: dict[str, Any], headers: dict[str, str] | None, timeout: float) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url, data=body, method="POST", headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")[:1000]
        raise RuntimeError(f"HTTP adapter returned {error.code}: {detail}") from error
    if not isinstance(result, dict):
        raise RuntimeError("Adapter response must be a JSON object")
    return result


def bridge_dispatch(tx: dict[str, Any], section: dict[str, Any]) -> dict[str, Any]:
    url = str(section.get("url") or DEFAULT_BRIDGE_URL)
    timeout = float(section.get("timeout_seconds") or 12)
    prompt = Path(tx["prompt_path"]).read_text(encoding="utf-8")
    submitted = post_json(url, {"op": "new_thread", "text": prompt, "cwd": tx["cwd"], "title": tx["title"],
                                "sourceThreadId": tx["session_id"]}, None, timeout)
    task_id = str(submitted.get("taskId") or "")
    if not task_id:
        raise RuntimeError(f"Bridge did not return taskId: {submitted}")
    status_url = url.rsplit("/api/local-tasks", 1)[0] + "/api/local-task/" + urllib.parse.quote(task_id)
    deadline = time.monotonic() + timeout
    latest = submitted
    while time.monotonic() < deadline:
        time.sleep(0.25)
        try:
            with urllib.request.urlopen(status_url, timeout=min(2.0, timeout)) as response:
                latest = json.loads(response.read().decode("utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if latest.get("threadId") or latest.get("status") in {"failed", "error"}:
            break
    if latest.get("status") in {"failed", "error"}:
        raise RuntimeError(str(latest.get("error") or latest.get("message") or "Bridge task failed"))
    return {"adapter": "bridge", "task_id": task_id, "thread_id": latest.get("threadId"), "adapter_result": latest}


def http_dispatch(tx: dict[str, Any], section: dict[str, Any]) -> dict[str, Any]:
    url = str(section.get("url") or "").strip()
    if not url:
        raise RuntimeError("[http].url is required")
    headers = section.get("headers") if isinstance(section.get("headers"), dict) else {}
    payload = {
        "operation": "new_task",
        "idempotency_key": f"{tx['chain_id']}:{tx['sequence']}",
        "title": tx["title"],
        "prompt": Path(tx["prompt_path"]).read_text(encoding="utf-8"),
        "cwd": tx["cwd"],
        "handoff_path": tx["handoff_path"],
        "source_thread_id": tx["session_id"],
    }
    result = post_json(url, payload, {str(k): str(v) for k, v in headers.items()}, float(section.get("timeout_seconds") or 15))
    return {"adapter": "http", "adapter_result": result, "thread_id": result.get("thread_id") or result.get("threadId"), "url": result.get("url")}


def command_dispatch(tx: dict[str, Any], section: dict[str, Any]) -> dict[str, Any]:
    command = section.get("command")
    if isinstance(command, str):
        argv = shlex.split(command, posix=os.name != "nt")
    elif isinstance(command, list):
        argv = [str(item) for item in command]
    else:
        raise RuntimeError("[command].command must be a string or array")
    payload = {
        "operation": "new_task",
        "idempotency_key": f"{tx['chain_id']}:{tx['sequence']}",
        "title": tx["title"],
        "prompt": Path(tx["prompt_path"]).read_text(encoding="utf-8"),
        "cwd": tx["cwd"],
        "handoff_path": tx["handoff_path"],
        "source_thread_id": tx["session_id"],
    }
    completed = subprocess.run(argv, input=json.dumps(payload, ensure_ascii=False), text=True, capture_output=True, timeout=float(section.get("timeout_seconds") or 30), check=False)
    if completed.returncode:
        raise RuntimeError(f"Command adapter failed ({completed.returncode}): {completed.stderr.strip()[:1000]}")
    try:
        result = json.loads(completed.stdout or "{}")
    except json.JSONDecodeError as error:
        raise RuntimeError("Command adapter stdout must be one JSON object") from error
    return {"adapter": "command", "adapter_result": result, "thread_id": result.get("thread_id") or result.get("threadId"), "url": result.get("url")}


def dispatch(args: argparse.Namespace) -> dict[str, Any]:
    path, record, tx = current_transaction(args)
    if tx.get("status") == "dispatched":
        return {"ok": True, "reused": True, **tx}
    if tx.get("status") not in {"ready", "dispatching"}:
        raise RuntimeError("Handoff is not ready. Write both files and run finalize first.")

    config, config_path = load_config(Path(tx["cwd"]))
    requested = str(args.adapter or (config.get("handoff") or {}).get("adapter") or "auto").lower()
    bridge_section = config.get("bridge") if isinstance(config.get("bridge"), dict) else {}
    command_section = config.get("command") if isinstance(config.get("command"), dict) else {}
    http_section = config.get("http") if isinstance(config.get("http"), dict) else {}
    if requested == "auto":
        bridge_url = str(bridge_section.get("url") or DEFAULT_BRIDGE_URL)
        if endpoint_reachable(bridge_url):
            requested = "bridge"
        elif command_section.get("command"):
            requested = "command"
        elif http_section.get("url"):
            requested = "http"
        else:
            requested = "manual"

    tx.update({"status": "dispatching", "adapter": requested, "config_path": config_path, "dispatch_started_at": now()})
    record["current"] = tx
    atomic_json(path, record)
    atomic_json(Path(tx["state_path"]), tx)
    try:
        if requested == "bridge":
            result = bridge_dispatch(tx, bridge_section)
        elif requested == "http":
            result = http_dispatch(tx, http_section)
        elif requested == "command":
            result = command_dispatch(tx, command_section)
        elif requested == "manual":
            result = {"adapter": "manual", "manual_required": True, "title": tx["title"], "prompt_path": tx["prompt_path"]}
        else:
            raise RuntimeError(f"Unknown adapter: {requested}")
    except Exception as error:
        tx.update({"status": "ready", "last_error": str(error), "last_error_at": now()})
        record["current"] = tx
        atomic_json(path, record)
        atomic_json(Path(tx["state_path"]), tx)
        raise

    tx.update(result)
    tx.update({"status": "dispatched" if requested != "manual" else "ready", "dispatched_at": now() if requested != "manual" else None})
    record["current"] = tx
    atomic_json(path, record)
    atomic_json(Path(tx["state_path"]), tx)
    return {"ok": True, "reused": False, **tx}


def status(args: argparse.Namespace) -> dict[str, Any]:
    _, _, tx = current_transaction(args)
    return {"ok": True, **tx}


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="action", required=True)
    for name in ("begin", "finalize", "dispatch", "status"):
        command = commands.add_parser(name)
        command.add_argument("--session-id")
        command.add_argument("--cwd", required=True)
        if name == "begin":
            command.add_argument("--mode", choices=("continuation", "split"), default="continuation")
        if name == "finalize":
            command.add_argument("--title", required=True)
            command.add_argument("--source-title", default="")
        if name == "dispatch":
            command.add_argument("--adapter", choices=("auto", "manual", "bridge", "http", "command"))
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        result = {"begin": begin, "finalize": finalize, "dispatch": dispatch, "status": status}[args.action](args)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
