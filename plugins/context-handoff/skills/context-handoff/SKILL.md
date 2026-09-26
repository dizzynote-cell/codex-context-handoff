---
name: context-handoff
description: Prepare and dispatch a durable Codex task handoff when the user says “确认交接”, asks to change conversations/tasks, or wants a long-running task transferred to a fresh conversation. Also initialize an older task's compaction count, or explain and configure compaction reminders and adapters. Do not use for ordinary summaries that are not intended to continue work in another task.
---

# Context Handoff

## Purpose

Carry the current task into a fresh top-level Codex task without pretending the workspace is cleaner or more complete than it is. Keep the handoff lightweight: preserve the decisions and breakpoint that matter, not a transcript.

## Initialize an older task

When the user sends the exact phrase `初始化老对话压缩计数` or `初始化当前老对话压缩计数`, let the plugin hook handle the request. It may backfill only from the current host-supplied transcript when that file exists and is readable. Do not infer a count from conversation length, summaries, or model memory, and do not accept a user-supplied arbitrary transcript path as a substitute.

Report the hook result. A successful import joins the normal listener: counts are merged by maximum rather than added, so retries do not duplicate history. If access is unavailable or the transcript format is not recognized, preserve the existing count and say that the historical count remains unknown.

## On “确认交接”

Treat an exact “确认交接” after the plugin reminder as authorization to perform the handoff now. Do not reinterpret it as permission to finish the feature, commit, deploy, clean the worktree, fix unrelated issues, or broaden testing.

You may wait for an already-running operation to finish or stop it safely. Then use the latest workspace state, even if many turns passed after the reminder.

## Workflow

1. Inspect the current objective, source task title and project grouping when available, recent decisions, relevant files, current diff/status, and verification evidence. Prefer read-only inspection.
2. Start or resume an idempotent transaction:

   `python <plugin-root>/scripts/context_handoff.py begin --session-id <session-id> --cwd <absolute-project-path>`

   Use the session ID supplied by the hook. For a user-requested handoff without hook context, omit it. Read the JSON result and reuse its paths if the transaction already exists.
3. Choose a concise title before writing the documents. If the source task is named `继续开发 N`, use `继续开发 N+1｜{current stage}`; the transaction's `sequence` numbers handoff files and is not the conversation number. If the source title is unknown, do not invent a numbered continuation. Keep the title understandable without opening the old task.
4. Write `handoff_path` and `prompt_path` using the structures below, with the chosen title and the source project's identity if known. Do not include secrets, raw long logs, hidden chain-of-thought, or obsolete requirements.
5. Mark the transaction ready:

   `python <plugin-root>/scripts/context_handoff.py finalize --session-id <session-id> --cwd <absolute-project-path> --title "<title>" --source-title "<actual-source-title>"`

   Omit `--source-title` only when the actual title is unavailable. The script checks and corrects the numbered continuation before dispatch; if it rejects a guessed number, use an unnumbered title.
6. Dispatch it:

   `python <plugin-root>/scripts/context_handoff.py dispatch --session-id <session-id> --cwd <absolute-project-path>`

   The script selects `manual`, `bridge`, `http`, or `command` from configuration and passes the source thread ID to compatible adapters so the new task can inherit its project grouping. Never create a subagent as the receiving task. If dispatch is manual, provide the returned title and prompt path/content and tell the user to create it in the source project. If it returns a thread/task ID or URL, report it. If project inheritance is unsupported, say so instead of claiming the new task is already grouped. If creation fails, leave the source task usable and report how to retry; do not create a second transaction.

## Handoff document

Keep it factual and compact. Include:

- Identity: chain ID, sequence, source session/task if known, target title, project path, timestamp, recorded compaction count.
- Current objective and exact scope.
- Confirmed user requirements.
- Decisions already made, with short reasons where they prevent rework.
- Completed work and important files.
- Current workspace/Git state, including relevant uncommitted changes without requiring cleanup.
- Exact breakpoint: what was happening when handoff was confirmed.
- Verification performed, results, and verification not yet performed.
- Remaining work in priority order.
- Known issues, risks, failed approaches, and things not to repeat.
- The single best first next action.

For a split handoff, explicitly state which track moves to the new task and which remains in the source task. Do not imply that the source task must close.

## Startup prompt

The receiving prompt should be short and action-oriented. It must contain:

- Absolute project path and handoff document path.
- Instruction to read the handoff and inspect the live workspace before changing files.
- Instruction to preserve existing user changes and report meaningful differences from the handoff.
- The exact breakpoint and first next action.
- Instruction not to reopen settled decisions unless the live workspace conflicts with them.

The new task does not need an approval ritual. After its read-only orientation, it may continue directly when the state matches.

## Safety and idempotency

- Repeated confirmation or retry must reuse an existing `preparing`, `ready`, `dispatching`, or `dispatched` transaction.
- A failed adapter must not mark the handoff dispatched.
- If a receiver was created but its first message is uncertain, preserve its returned ID and retry that receiver rather than creating another.
- Never expose credentials from config or environment in the documents or response.
