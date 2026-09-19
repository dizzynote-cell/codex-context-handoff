# Context Handoff

一个面向长时间 Codex 开发任务的轻量交接插件。

它不会逐轮分析或消耗模型上下文。插件只在 Codex 的压缩事件发生后更新一个很小的本地状态文件：从第 4 次上下文压缩起，每次压缩提醒一次。提醒以后，用户可以在任意轮次回复 `确认交接`，Codex 会按回复当时的真实项目状态生成交接材料。

## 工作方式

1. `PostCompact` Hook 对每个任务独立计数；同一压缩事件重试不会重复计数。
2. 第 4 次及以后显示交接提醒。
3. `UserPromptSubmit` Hook 只识别完整指令 `确认交接`，并让 `context-handoff` Skill 接管。
4. Skill 生成完整交接文档和精简启动提示词。
5. 适配器创建新的顶层任务；环境不支持时回退为手动方式。

交接文件默认位于项目内：

```text
.codex/handoffs/<chain-id>/
  HANDOFF_001.md
  START_PROMPT_001.md
  STATE_001.json
```

## 新任务适配器

- `manual`：始终可用，返回建议标题和启动提示词路径。
- `bridge`：调用 CodexFeishuBridge 的本机 `/api/local-tasks`，创建正常的顶层 Codex 任务并发送第一条消息。
- `http`：面向其他外壳的通用 JSON HTTP 协议。
- `command`：面向本机工具的 JSON stdin/stdout 协议。
- `auto`：依次考虑本机 Bridge、已配置的 command/http，最后回退 manual。

复制 `config.example.toml` 到用户级 `~/.codex/context-handoff.toml` 或项目级 `.codex/context-handoff.toml` 后修改。也可用环境变量 `CONTEXT_HANDOFF_CONFIG` 指定配置文件。

## 安装注意

启用插件后，需要在 Codex 中审查并信任插件 Hook；Codex 不会自动信任第三方 Hook。Hook 脚本需要本机有 Python 3.11 或更高版本。只使用 `manual` 且没有配置文件时，核心脚本也可在更早的 Python 3 版本运行。

## 交接边界

`确认交接` 不会自动提交、部署、清理、回滚或补完功能。未提交修改会如实写入交接。若旧任务还需要保留另一条工作线，可使用 split 模式，新的任务只接走指定分支。

## 开源

MIT License。Bridge 只是可选适配器；其他外壳不需要安装 Bridge，只需实现 HTTP 或 command 适配器契约。
