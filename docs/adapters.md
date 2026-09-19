# 自制 Codex 外壳接入

外壳是自己搭建的 Codex 界面，例如网页控制台或供手机访问的页面。这里的配置负责调用外壳创建新对话；压缩提醒仍需要运行 Codex 的后端支持 Hook。普通用户无需接入外壳，手动新建即可。

## 选择方式

在配置文件中设置 `[handoff].adapter`：

| 值 | 行为 |
|---|---|
| `manual` | 生成材料，用户手动新建 |
| `http` | 向指定接口发送创建请求 |
| `command` | 运行本机程序创建对话 |
| `bridge` | 使用已有的特定本机接口协议 |
| `auto` | 默认：探测本机接口，然后选择已配置的 command、http，最后使用 manual |

配置按以下顺序选用第一个存在的文件，不合并：环境变量 `CONTEXT_HANDOFF_CONFIG` 指定的文件 → 项目配置 → 用户配置。

## HTTP 接口

```toml
[handoff]
adapter = "http"

[http]
url = "http://127.0.0.1:9000/codex/new-task"
timeout_seconds = 15
```

接口收到 JSON POST，包含 `operation="new_task"`、`idempotency_key`、`title`、`prompt`、`cwd` 和 `handoff_path`。外壳负责创建普通对话、设置标题并发送首条消息，返回 JSON 对象，例如：

```json
{"thread_id": "created-thread-id", "url": "https://your-shell.example/task/created-thread-id"}
```

失败时返回非成功 HTTP 状态，并利用 `idempotency_key` 防止重复创建。路径指向运行插件的机器；远程外壳需要能访问同一项目及交接文件。认证可通过 `[http.headers]` 配置，勿提交真实凭据。

## 本机命令

```toml
[handoff]
adapter = "command"

[command]
command = ["python", "C:/tools/create_task.py"]
timeout_seconds = 30
```

程序从标准输入读取与 HTTP 相同的 JSON，标准输出返回一个 JSON 对象。日志写到标准错误；失败返回非零退出码。推荐使用参数数组。

## 内置本机接口

`bridge` 是为 CodexFeishuBridge 接口提供的兼容模式，并非所有外壳通用。其他外壳推荐使用 HTTP 或命令方式，无需安装该项目。

默认地址为 `http://127.0.0.1:8765/api/local-tasks`。发送 `op="new_thread"`、`text`、`cwd`、`title`，取得 `taskId` 后查询 `/api/local-task/<taskId>`。

当前 auto 只检查端口可连接，不验证服务身份。若该端口运行其他服务，请明确选择 manual、http 或 command。自动派发报错后，应先检查是否已创建对话再重试；当前版本不保证网络中断时恰好创建一次。
