# Context Handoff for Codex

Get a reminder when a conversation grows long, then prepare the notes needed to continue in a fresh conversation.

Starting with the fourth recorded context compaction, the plugin reminds you after each compaction. Compaction condenses history; it is not a chat-turn count or proof of errors. Events before installation are not backfilled.

## Install and use

Requires Codex with local plugin hooks and Python 3.11+ available as `python`.

```bash
codex plugin marketplace add dizzynote-cell/codex-context-handoff
codex plugin add context-handoff@context-handoff
```

Start a new task and review/trust the hooks. The skill and scripts are included.

After a reminder, send the exact phrase `确认交接` in a later message. This means “confirm handoff” and is currently the automatic trigger.

Codex prepares handoff notes and a startup prompt from the latest task state. A compatible interface can create the receiving conversation automatically. Otherwise, create one yourself and paste the prompt. Existing uncommitted work is preserved.

## Configuration

No configuration is required. The default probes a compatible local interface and otherwise supplies materials for manual creation.

To always create conversations yourself, put this in your user or project `.codex/context-handoff.toml`:

```toml
[handoff]
adapter = "manual"
```

Project configuration takes precedence. A custom Codex UI can connect through HTTP or a local command; see the [adapter guide (Chinese)](adapters.md) and [configuration example](../plugins/context-handoff/config.example.toml).

## Files and compatibility

Notes and prompts are saved under the project's `.codex/handoffs/`. Counters are local and there is no added telemetry. Automatic dispatch sends the startup prompt to the selected interface or program, which passes it to Codex.

Automatic reminders require hooks on the machine running Codex, including when accessed through a mobile browser. A web environment that cannot run local scripts cannot provide automatic reminders.

Windows script simulations and structural validation have been performed. Cross-platform behavior and actual reminder presentation in each client still need verification.
