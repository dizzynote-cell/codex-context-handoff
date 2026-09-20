from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hook_state import backfill_current_session, load_state


def is_confirmation(prompt: object) -> bool:
    normalized = re.sub(r"[。.!！?？\s]+$", "", str(prompt or "").strip())
    return normalized == "确认交接"


def is_initialization(prompt: object) -> bool:
    normalized = re.sub(r"[。.!！?？\s]+$", "", str(prompt or "").strip())
    return normalized in {"初始化老对话压缩计数", "初始化当前老对话压缩计数"}


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return 0
    if is_initialization(event.get("prompt")):
        session_id = event.get("session_id") or event.get("sessionId") or "unknown-session"
        try:
            state = backfill_current_session(
                session_id,
                event.get("transcript_path") or event.get("transcriptPath"),
                event.get("cwd"),
            )
        except ValueError as error:
            print(json.dumps({
                "systemMessage": f"老对话压缩计数初始化失败：{error}。未修改现有计数，也不会猜测历史次数。"
            }, ensure_ascii=False))
            return 0
        count = int(state.get("compaction_count") or 0)
        status = "已进入可交接状态" if count >= 4 else "尚未达到第 4 次提醒阈值"
        print(json.dumps({
            "systemMessage": (
                f"已从当前任务的本机会话记录初始化压缩计数：{count} 次，{status}。"
                "后续压缩将继续由 PostCompact 监听；重复初始化不会重复累计。"
            )
        }, ensure_ascii=False))
        return 0
    if not is_confirmation(event.get("prompt")):
        return 0

    session_id = event.get("session_id") or event.get("sessionId") or "unknown-session"
    state = load_state(session_id)
    if not state.get("eligible"):
        return 0

    count = int(state.get("compaction_count") or 0)
    cwd = str(event.get("cwd") or state.get("cwd") or "")
    context = f"""Context Handoff 插件检测到用户在交接提醒后明确回复“确认交接”。
这是执行交接的授权，不是继续扩展当前开发工作的指令。当前会话 ID：{session_id}；已记录压缩次数：{count}；工作目录：{cwd}。
现在必须使用 context-handoff Skill：以此刻真实状态为准，停止新增范围；只允许等待已在运行的命令结束或做安全停止。生成完整交接文档与精简的新任务首条提示词，然后调用插件脚本完成或尝试派发。不要因为仓库有未提交修改而强制提交、清理或回滚。若自动创建不可用，清楚展示手动新建任务所需的标题和首条提示词。重复执行时复用当前交接事务，不要创建重复任务。"""
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": context,
        }
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
