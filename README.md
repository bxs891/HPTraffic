# HPTraffic Orchestrator (OpenAI Agents SDK)

实现了一个基于 OpenAI Agents SDK 的编排流程：

1. `agent_collect` 调用 `collector_tool` 获取 `posts`
2. handoff 给 `agent_detect`
3. handoff 给 `agent_score`
4. `agent_score` 最后调用 `notify_tool`

并满足以下要求：

- 使用 `trace(...)` 保留 trace 信息，并在日志中打印 `trace_id`
- 每次运行将结果写入 SQLite 数据库 `traffic_runs.db`

## 运行

```bash
python orchestrator.py
```

> 运行前请确保已配置模型与 OpenAI Agents SDK 所需环境变量。

## 数据落库

表名：`traffic_runs`

字段：
- `trace_id`
- `topic`
- `posts_json`
- `detected_json`
- `scored_json`
- `notify_json`
- `created_at`
