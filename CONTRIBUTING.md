# Contributing

Issues and pull requests are welcome.

## Development principles

- Keep compaction counting deterministic and inexpensive; do not add per-turn model monitoring.
- Preserve the user's live workspace state. A handoff must not imply permission to commit, clean, deploy, roll back, or finish unrelated work.
- Keep adapters optional. The manual path must remain functional without CodexFeishuBridge or another shell.
- Never write secrets, hidden reasoning, or raw long logs into handoff documents.
- Preserve idempotency: retries must not intentionally create duplicate receiving tasks.

## Testing

Before opening a pull request:

1. Validate the plugin and the bundled skill.
2. Simulate at least five unique `PostCompact` events and verify that only events four and later display reminders.
3. Verify that `确认交接` is recognized only after the session becomes eligible.
4. Verify that beginning the same handoff twice reuses the same transaction.
5. Verify the `manual` adapter before testing any adapter that creates an external task.

Do not include generated `.codex/handoffs`, plugin data, credentials, or Python bytecode in commits.
