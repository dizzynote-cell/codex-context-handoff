# Context Handoff for Codex

[中文](#中文) · [English](#english)

## 中文

Context Handoff 是一个面向长时间 Codex 开发任务的开源插件。它从第 4 次上下文压缩开始提醒用户；提醒后，用户可以在任何后续轮次回复 `确认交接`，让 Codex 根据当时的真实项目状态整理交接材料，并在环境支持时创建新的顶层任务。

### 为什么同时包含 Hook 和 Skill

- Hook 负责记录压缩次数、显示提醒和识别明确的交接确认。
- Skill 负责决定交接材料应包含什么、如何保护未提交修改，以及新任务应该怎样接手。
- Plugin 是用户安装的唯一发布单位，已经同时包含二者。
- CodexFeishuBridge 只是可选适配器；没有安装 Bridge 也能使用手动交接。

### 安装

要求：支持本地插件和 Hook 的 Codex 客户端，以及可通过 `python` 命令调用的 Python 3.11 或更高版本。

```bash
codex plugin marketplace add dizzynote-cell/codex-context-handoff
codex plugin add context-handoff@context-handoff
```

安装后新建一个 Codex 任务。首次运行时请审查并信任插件 Hook，否则自动压缩计数不会执行。

### 使用

正常使用 Codex 即可。第 4 次上下文压缩完成后会看到提醒；以后任意轮次回复：

```text
确认交接
```

插件不会强制提交、部署、清理或回滚工作区。默认交接文件写入：

```text
.codex/handoffs/<chain-id>/
  HANDOFF_001.md
  START_PROMPT_001.md
  STATE_001.json
```

### 新任务创建方式

| 适配器 | 用途 |
|---|---|
| `manual` | 始终可用，给出新任务标题和首条提示词 |
| `bridge` | 调用 CodexFeishuBridge 的本机接口创建顶层 Codex 任务 |
| `http` | 适配其他带 HTTP 接口的 Codex 外壳 |
| `command` | 通过 JSON stdin/stdout 适配本机程序 |
| `auto` | 自动尝试可用适配器，最后回退到 `manual` |

复制 [`config.example.toml`](plugins/context-handoff/config.example.toml) 到 `~/.codex/context-handoff.toml` 或项目的 `.codex/context-handoff.toml` 进行配置。

### 隐私与安全

- 压缩计数和交接事务状态保存在本机。
- 插件本身不提供遥测，也不会主动上传对话或项目内容。
- 只有配置 HTTP 或 Bridge 适配器后，启动提示词才会发送给对应的本机或自定义端点。
- Hook 在获得用户信任前不会运行。

### 当前限制

- 自动压缩计数依赖本地 Codex Hook；不支持本地 Hook 的网页或移动环境只能使用 Skill 的手动交接能力。
- 自动创建新任务取决于宿主是否提供接口。官方客户端没有可用接口时会回退到手动方式。
- 当前版本主要在 Windows 上验证，欢迎提交 macOS 和 Linux 兼容性反馈。

## English

Context Handoff is an open-source Codex plugin for long-running development tasks. Starting with the fourth context compaction, it reminds the user that the task can be handed off. At any later turn, the user can reply `确认交接` to generate durable handoff documents from the latest workspace state.

The plugin bundles both lifecycle hooks and a reusable skill. Hooks provide deterministic compaction counting and confirmation detection; the skill defines the semantic handoff workflow. CodexFeishuBridge is optional.

### Install

Requirements: a Codex client that supports local plugins and hooks, plus Python 3.11+ available as `python`.

```bash
codex plugin marketplace add dizzynote-cell/codex-context-handoff
codex plugin add context-handoff@context-handoff
```

Start a new Codex task after installation and review/trust the bundled hooks when prompted.

### Configure

Copy [`config.example.toml`](plugins/context-handoff/config.example.toml) to `~/.codex/context-handoff.toml` or `.codex/context-handoff.toml`. Available adapters are `auto`, `manual`, `bridge`, `http`, and `command`.

### Privacy

State is stored locally. The plugin has no telemetry and does not upload conversations or project files. A startup prompt is sent externally only when the user configures an HTTP-style adapter.

## Development

Plugin source: [`plugins/context-handoff`](plugins/context-handoff)

Validate before submitting changes:

```bash
python path/to/plugin-creator/scripts/validate_plugin.py plugins/context-handoff
python path/to/skill-creator/scripts/quick_validate.py plugins/context-handoff/skills/context-handoff
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## License

[MIT](plugins/context-handoff/LICENSE)
