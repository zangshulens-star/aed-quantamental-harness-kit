# Handoff Blob — 规范

> 子代理上下文注入的最小协议：一个 ~200 词的文本块，让新启动的 agent 在零上下文下立即知道"我在哪个项目、现在干什么、刚做完什么、关键文件在哪"。
> 与 Task Tracking Protocol 配套使用（TTP §3 Agent Handoff）。

---

## 1. 格式

```
[HANDOFF]
Project: <项目名>
About: <一句话描述——项目做什么>
Stack: <技术栈一行>
Main task: <当前主线任务>
Status: <main | branched>
Done: <最近完成的里程碑（一句话）>
Key files: <3-5 个关键路径>
Next: <下一步动作（一句话）>
[/HANDOFF]
```

**硬约束**：
- 总长度 **≤200 词**——它是 prompt 前缀，不是文档。超过 200 词说明 Snapshot 该减肥了
- 标记固定为 `[HANDOFF]` / `[/HANDOFF]`——提取方按标记切分，不得改动
- 每个字段一行，字段名固定（消费方正则解析）

---

## 2. 用途与用法

**什么时候生成**：每次 spawn 子代理前。主 agent 从 `.claude/current_task.md` 的 Handoff Blob 段提取（标记之间），原样前置到子代理 prompt：

```
[HANDOFF]
{Handoff Blob 原文}
[/HANDOFF]

Specific task: {给子代理的具体指令}
```

**为什么有效**：子代理从零上下文启动。没有 Blob 时，主 agent 要么写一大段背景（每次手写、格式漂移、漏关键信息），要么让子代理自己翻项目（烧 token 且可能读错文件）。Blob 把"项目身份 + 当前任务态"压缩成固定格式的 200 词，**传输成本恒定、格式可机器校验**。

**什么时候更新**：
- 任务状态变化（新 ticket / 完成 / converge）→ 立即重写 current_task.md，Blob 随之更新
- 大里程碑（阶段完成、新 agent 上线、架构变更）→ 更新 Project Snapshot，Blob 重新生成

---

## 3. 生成规则

从 Project Snapshot 合成，字段对应关系：

| Blob 字段 | 来源 |
|-----------|------|
| Project / About | Snapshot `Identity` |
| Stack | Snapshot `Architecture` 的技术栈摘要 |
| Main task / Status | Task Index 的 `main` / `status` |
| Done | 最近一个完成的 ticket 或里程碑 |
| Key files | Snapshot `Key Paths` 中最关键的 3-5 个 |
| Next | Task Index 的下一个 pending ticket |

**纪律**：
- Blob 是**派生物**，不可手工编辑——改源头（current_task.md / Snapshot）后重新生成
- 不放的比放的重要：不放历史、不放细节、不放数字表——那些属于 docs/，不属于 prompt 前缀
- 敏感信息（凭证、内部路径、人名）不得进 Blob——它会被复制到子代理上下文，传播面不可控

---

## 4. 示例

```
[HANDOFF]
Project: Aurora Pricing Engine
About: Real-time derivative pricing service for the rates desk
Stack: Python 3.12, FastAPI, Redis cache, LangGraph orchestration
Main task: Migrate pricing cache from in-process to Redis
Status: branched (T12 cache invalidation)
Done: T11 completed — Redis connection layer + failover tests green
Key files: src/cache/redis_layer.py, src/pricing/engine.py, docs/architecture/02_cache.md
Next: user reviews invalidation strategy doc, then converge T12
[/HANDOFF]
```
