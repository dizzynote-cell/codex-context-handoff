# Context Handoff

对话太长时提醒换对话，并整理接着做所需的材料。

从插件记录的第 4 次上下文压缩开始，每次压缩提醒一次。提醒后，在任意后续轮次单独回复 `确认交接`，即可生成交接文档和新对话启动提示词。有兼容接口时自动创建新对话，否则由用户手动新建并粘贴提示词。

安装前已经使用过的老对话，可以在该对话中发送 `初始化老对话压缩计数`。当宿主提供可读的本机会话记录时，插件会补入结构化压缩事件并接入后续监听；没有权限或记录不可识别时不会猜数。

Skill、Hook 和脚本已包含在插件内。需要支持本地 Hook 的 Codex、Python 3.11+（命令为 `python`），以及用户对 Hook 的信任。

默认无需配置。若希望始终手动新建，在用户目录或项目的 `.codex/context-handoff.toml` 写入：

```toml
[handoff]
adapter = "manual"
```

交接材料保存在项目的 `.codex/handoffs/`，现有未提交修改会保留。

- [安装与使用](https://github.com/dizzynote-cell/codex-context-handoff#readme)
- [自制 Codex 外壳接入](https://github.com/dizzynote-cell/codex-context-handoff/blob/main/docs/adapters.md)
- [配置示例](config.example.toml)
