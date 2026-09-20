# Security Policy

Please report security issues privately through GitHub's security advisory feature instead of opening a public issue.

Context Handoff runs local lifecycle hooks after the user explicitly trusts them. Review `plugins/context-handoff/hooks/hooks.json` and the referenced scripts before enabling the hooks.

The plugin uses two hooks:

- `PostCompact` updates the local compaction count and emits a reminder beginning with the fourth recorded compaction.
- `UserPromptSubmit` receives each submitted prompt because Codex does not support a matcher for this event. It performs exact local comparisons with `确认交接` and the documented old-task initialization phrases. Non-matching prompts exit without being stored or transmitted.

Old-task initialization is permission-bound. It reads only the current `transcript_path` supplied by the Codex host, never a path supplied inside the prompt. The script streams the local JSONL file, counts structured `compacted` events, and does not persist or output message bodies. If the file is missing, unreadable, belongs to another session, or has no recognizable events, it preserves the existing count and reports failure.

The hooks do not make network requests, call a model, modify business files, or run Git and deployment commands. They store only compaction state and transaction metadata locally. Handoff files are created only after explicit confirmation.

When an adapter is configured or a compatible local interface is detected, the confirmed handoff startup prompt is sent to that process so it can create the receiving conversation. Set `adapter = "manual"` to disable automatic dispatch.

These properties reduce the default attack surface but do not make every installation or future version inherently safe. Verify the repository source, the exact hook commands shown by `/hooks`, and any changed hook definition before granting trust. Codex ties trust to the current hook definition and requests another review after it changes.

Do not place credentials in handoff documents. Keep adapter credentials in local configuration and exclude that configuration from source control.
