# Context Handoff for Codex

Get a reminder when a conversation grows long, then prepare the notes needed to continue in a fresh conversation.

Starting with the fourth recorded context compaction, the plugin reminds you after each compaction. Compaction condenses history; it is not a chat-turn count or proof of errors. Events before installation are not backfilled.

## Why hooks and the fourth compaction

Semantic drift is difficult for the active model to diagnose reliably. A model that has already forgotten an early constraint may still believe its current interpretation is correct, so drift may only become visible after a user correction, file conflict, or failed check. This plugin therefore uses an observed Codex compaction event instead of the model's subjective assessment as its primary trigger.

The threshold is based on the maintainer's long-term practical experience with Codex 5.6 and later models: in the observed development work, a material misunderstanding requiring an immediate conversation change was rarely seen within the first four context compactions. This is the empirical reason for the default, not a universal accuracy guarantee across models, tasks, or users.

The safety margin also draws on one long-running conversation of more than 200 turns, where the maintainer noticed slight drift around the eighth or ninth context compaction and concluded that even slight drift was enough reason not to keep relying on the same conversation for later work. Beginning reminders at the fourth compaction is intended to leave about four to five compactions in which to hand off before slight drift appears, rather than reacting after it has already begun. This remains a single practical observation, not a claim that every task drifts at the same point.

That margin is also useful in long-running automation and multi-agent workflows. When every Codex task that needs protection has the hook enabled and the orchestration handles reminders and performs handoffs, it can reduce the chance that a top-level task continues unattended with increasingly distorted context. It cannot guarantee that every independent agent or inter-agent message is correct, and it does not force a task switch without confirmation.

The rule is deliberately simple:

- Do not interrupt the first three compactions.
- Starting with the fourth, remind after every real compaction.
- Do not require the model to identify a new work stage or wait through another cooldown period.
- A reminder neither proves an error nor starts a handoff; the user remains in control.

The algorithm does not claim to predict drift. Its advantage is a deterministic, transparent, and testable handoff checkpoint after risk has increased.

## Install and use

Requires Codex with local plugin hooks and Python 3.11+ available as `python`.

```bash
codex plugin marketplace add dizzynote-cell/codex-context-handoff
codex plugin add context-handoff@context-handoff
```

Start a new task and review/trust the hooks. The skill and scripts are included.

### Enable and inspect the hooks

1. Start a new Codex task after installation.
2. Enter `/hooks` in the Codex CLI.
3. Review `PostCompact` and `UserPromptSubmit`, verify that their commands point into this plugin, and mark them as trusted.
4. Confirm that both show `Installed 1` and `Active 1`.
5. Codex requires another review if a hook definition changes; untrusted hooks are skipped.

If a graphical client does not expose the full hook manager, use the Codex CLI on the same machine. On Windows, `codex.cmd` can be used when PowerShell blocks `codex.ps1`.

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

## Hook security boundary

Hooks execute public Python scripts locally, so review them as you would any local automation before trusting them in `/hooks`.

- `PostCompact` runs after compaction. It updates a local count and returns a reminder. It does not store the full conversation.
- `UserPromptSubmit` starts for every submitted prompt because Codex currently provides no content matcher for this event. It only checks whether the normalized prompt exactly equals `确认交接`; ordinary prompts exit immediately and are neither persisted nor sent over the network.
- The hooks do not call a model, modify project business files, commit or deploy code, or add telemetry.
- Handoff files are written only after explicit confirmation. A startup prompt is sent to another local interface or program only when a compatible adapter is configured or detected.

This is a deliberately narrow capability boundary, not a claim that arbitrary local scripts are absolutely safe. Users should review the source, command definitions, installation source, and changed hooks before trusting them.
