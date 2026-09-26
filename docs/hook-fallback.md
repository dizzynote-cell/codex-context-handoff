# 插件 Hook 未显示时的备用配置

仅当插件已经安装、启用，但 `/hooks` 中 `PostCompact` 和 `UserPromptSubmit` 仍显示 `0/0` 时使用。Codex CLI 0.156.1 的 Windows 安装曾出现这种情况。

1. 重新运行 `codex plugin add context-handoff@context-handoff`，记下输出中的 `Installed plugin root` 绝对路径。Windows PowerShell 若阻止 `codex.ps1`，使用 `codex.cmd`。
2. 在用户级 `~/.codex/config.toml` 中加入以下配置，把 `<PLUGIN_ROOT>` 替换为刚才的实际路径。Windows 路径放在 TOML 单引号内，不必转换反斜杠。

```toml
[[hooks.PostCompact]]
[[hooks.PostCompact.hooks]]
type = "command"
command = 'python -X utf8 "<PLUGIN_ROOT>\hooks\post_compact.py"'

[[hooks.UserPromptSubmit]]
[[hooks.UserPromptSubmit.hooks]]
type = "command"
command = 'python -X utf8 "<PLUGIN_ROOT>\hooks\user_prompt_submit.py"'
```

3. 重新启动 Codex，审查并信任这两个来源为 `User config` 的 Hook。输入 `/hooks`，确认两项的 `Installed` 和 `Active` 均为 `1`。

如果将来插件自身的 Hook 也能被加载，先移除上述用户级重复配置，避免同一个事件执行两遍。更新插件后还要检查缓存路径是否变化；路径变化时需更新命令并重新信任。
