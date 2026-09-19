# Auto Context Handoff for Codex/Codex自动上下文交接插件

对话太长时，提醒你换一个新对话，并帮你整理接着做所需的材料。

从插件记录的**第 4 次上下文压缩（大概50-80轮对话）**开始，每次压缩后提醒一次。你可以继续工作，也可以在之后任意一轮单独回复 `确认交接`。Codex 会整理当前目标、已完成工作、重要决定和下一步，生成交接文档与新对话的首条提示词。

> 上下文压缩，是 Codex 为容纳后续内容而浓缩历史对话的过程。这里统计的是压缩次数，不是聊天轮数；第 4 次是提醒规则，不代表任务已经出错。安装前的压缩不自动补计。

## 安装

需要支持本地插件及生命周期钩子（Hook）的 Codex，以及能通过 `python` 命令运行的 Python 3.11+。

```bash
codex plugin marketplace add dizzynote-cell/codex-context-handoff
codex plugin add context-handoff@context-handoff
```

安装后打开新任务，并按客户端提示审查、信任插件 Hook。Skill 和脚本已经包含在插件内，无需分别安装。

## 怎么用

1. 正常使用 Codex，等待交接提醒。
2. 想换对话时，单独发送：`确认交接`。
3. 插件生成交接文档和启动提示词。有兼容的创建接口时自动新建对话；否则，你新建对话并粘贴生成的提示词。

交接以确认时的最新状态为准，保留未提交修改，不要求先提交代码或完成当前功能。材料保存在项目的 `.codex/handoffs/` 下：

- `HANDOFF_001.md`：项目进度与背景，给接手对话阅读。
- `START_PROMPT_001.md`：粘贴到新对话的首条消息。
- `STATE_001.json`：插件进度记录，无需手动编辑。

## 需要配置吗？

**普通使用无需配置。** 默认尝试本机兼容接口，没有接口就生成材料供你手动新建对话。并不是所有 Codex 客户端或自制外壳都支持自动创建。

如果希望始终手动新建，在用户目录的 `.codex/context-handoff.toml` 中写入：

```toml
[handoff]
adapter = "manual"
```

Windows 路径示例：`C:/Users/你的用户名/.codex/context-handoff.toml`。也可以放进项目的 `.codex/context-handoff.toml`，仅对该项目生效，项目配置优先。

如果你使用**自制 Codex 外壳**（例如自己搭建的网页或手机访问界面），可以让插件调用它的创建对话接口。外壳需要先按协议接入，填写任意网址并不能直接生效。参见[外壳接入说明](docs/adapters.md)和[配置示例](plugins/context-handoff/config.example.toml)。

## 适用范围与数据

自动提醒取决于运行 Codex 的机器是否支持并启用了 Hook。用手机访问自制网页也可以，前提是后端支持；仅安装到不运行本地脚本的网页环境不会获得自动提醒。

计数保存在本机，插件没有额外遥测。自动创建对话时，启动提示词会交给所选接口或程序，再由它发送给 Codex。默认模式会探测本机接口；如不希望使用它，设置 `manual`。

目前完成了 Windows 上的脚本模拟与结构校验；跨平台兼容性和各客户端实际提醒显示仍需进一步验证。

[English](docs/README.en.md) · [贡献指南](CONTRIBUTING.md) · [安全说明](SECURITY.md) · [MIT 许可证](plugins/context-handoff/LICENSE)
