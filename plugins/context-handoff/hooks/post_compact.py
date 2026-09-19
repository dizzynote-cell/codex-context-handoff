from __future__ import annotations

import json
import sys
from datetime import datetime, timezone

from hook_state import load_state, save_state


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return 0

    session_id = event.get("session_id") or event.get("sessionId") or "unknown-session"
    turn_id = str(event.get("turn_id") or event.get("turnId") or "")
    state = load_state(session_id)
    seen = list(state.get("compact_turn_ids") or [])

    # A hook may be retried. Count a compaction turn only once.
    if turn_id and turn_id in seen:
        return 0

    state["compaction_count"] = int(state.get("compaction_count") or 0) + 1
    if turn_id:
        seen.append(turn_id)
        state["compact_turn_ids"] = seen[-64:]
    state["eligible"] = state["compaction_count"] >= 4
    state["last_compaction_at"] = datetime.now(timezone.utc).isoformat()
    state["cwd"] = str(event.get("cwd") or state.get("cwd") or "")
    save_state(session_id, state)

    count = state["compaction_count"]
    if count < 4:
        return 0
    if count == 4:
        message = (
            "当前任务已完成第 4 次上下文压缩，现已进入可交接状态。任务可以继续；"
            "此后你可以在任意轮次回复“确认交接”，系统会按届时的最新项目状态生成交接材料，"
            "并在当前环境支持时创建接手任务。"
        )
    else:
        message = (
            f"当前任务已完成第 {count} 次上下文压缩，仍处于可交接状态。"
            "需要时回复“确认交接”即可按最新状态交接。"
        )
    print(json.dumps({"systemMessage": message}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
