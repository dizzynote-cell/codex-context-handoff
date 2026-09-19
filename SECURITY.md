# Security Policy

Please report security issues privately through GitHub's security advisory feature instead of opening a public issue.

Context Handoff runs local lifecycle hooks after the user explicitly trusts them. Review `plugins/context-handoff/hooks/hooks.json` and the referenced scripts before enabling the hooks.

The plugin stores compaction counters and transaction metadata locally. It sends a startup prompt to another process only when an adapter is configured or a compatible local bridge is detected. Do not place credentials in handoff documents. Keep adapter credentials in local configuration and exclude that configuration from source control.
