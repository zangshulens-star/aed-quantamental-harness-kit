# Task Tracking Protocol — Upgrade Kit v1.0

> **用途**: 将 Task Tracking Protocol 移植到任意 Claude Code 项目。
> **方式**: 人工复制粘贴 或 Agent 自主执行。
> **前置**: 目标项目已有 CLAUDE.md。

---

## Kit Contents

| 文件 | 用途 |
|------|------|
| `TASK_TRACKING_PROTOCOL.md` | 完整协议规范 (参考文档，不必须复制) |
| `UPGRADE_KIT.md` | 本文件 — 升级工具包 |
| `current_task.md` (模板) | 任务状态文件模板 |

---

## Step 1: Inject CLAUDE.md Protocol Block

在目标项目 CLAUDE.md 末尾（`## 环境` section 之前）插入以下 block:

````markdown
## Task Tracking Protocol (mandatory)

### 1. Startup Recovery
- Every turn start: Read `.claude/current_task.md`
- If file missing: Initialize from project metadata (see Bootstrapping below)

### 2. Branch Management
- New sub-task identified: append ticket to Task Index, set `status: branched`
- Sub-task completed: mark ticket `[x]`, **MUST ask user**: "Close ticket and converge to main?"
- User confirms converge: update converge pointer, set `status: main`
- User defers: keep `status: branched`, continue next sub-task
- **NEVER silently switch between main and branched without user confirmation**

### 3. Agent Handoff
- Before spawning Agent via Agent tool:
  a) Read `.claude/current_task.md`
  b) Extract Handoff Blob section (between `[HANDOFF]` and `[/HANDOFF]`)
  c) Prepend to Agent prompt:
     ```
     [HANDOFF]
     {Handoff Blob content verbatim}
     [/HANDOFF]

     Specific task: {detailed instruction}
     ```
- The Handoff Blob gives the Agent project identity + current task state in ~200 words

### 4. State Persistence
- Task status change (new ticket, ticket complete, converge) → Write `.claude/current_task.md` immediately
- Turn end → Verify `.claude/current_task.md` reflects latest state
- Project Snapshot → update on major milestones (phase complete, new agent, architecture change)

### Bootstrapping (first-time init)
When `.claude/current_task.md` is missing:
1. Read `docs/ENGINEERING_INDEX.md` (or `CLAUDE.md` if no index exists)
2. Extract: project name, description, tech stack, key paths
3. Initialize Task Index: main = user's first request, status = main, tickets = []
4. Generate Project Snapshot + Handoff Blob from metadata
5. Write `.claude/current_task.md`
6. Report: "Task tracking initialized. Current main: <X>"
````

---

## Step 2: Create .claude/current_task.md

创建 `.claude/current_task.md` 文件，填入目标项目的 metadata。

### 模板

```markdown
# Task Index

main:     <当前主线任务描述>
status:   main
tickets:
converge: —

---

## Project Snapshot
> Generated: <YYYY-MM-DD> | Source: <docs/ENGINEERING_INDEX.md | CLAUDE.md>

### Identity
<project name> — <one-line description>

### Architecture
- <tech stack summary>
- <agent/module count and structure>
- <key architecture decisions>

### Key Paths
- Main index: <path>
- Architecture: <path>
- Agent root: <path>
- Data: <path>

---

## Handoff Blob
> Auto-generated at agent spawn time.

[HANDOFF]
Project: <project name>
About: <one-line description>
Stack: <tech stack>
Main task: <current mainline>
Status: main
Done: <last completed milestone>
Key files: <3-5 critical paths>
[/HANDOFF]
```

---

## Step 3: Verify

1. Re-read CLAUDE.md — confirm protocol block is present
2. Re-read `.claude/current_task.md` — confirm Project Snapshot reflects actual project
3. Ask user: "What is the current main task?" — align Task Index main line
4. Confirm: next turn, the LLM reads `.claude/current_task.md` as first action

---

## Agentic Self-Execution Prompt

Copy the prompt below and give it to any Claude Code agent to execute the upgrade autonomously:

```
You are executing a harness upgrade: install the Task Tracking Protocol into
this project. Follow these steps exactly. Do not skip verification.

STEP 1 — Audit target project
- Read CLAUDE.md. Note its current structure and where to insert the protocol
  block (before "## 环境" or equivalent final section).
- Read docs/ENGINEERING_INDEX.md if it exists. Extract: project name,
  one-line description, tech stack, key directory paths, agent/module count.
- If no ENGINEERING_INDEX.md, extract the same info from CLAUDE.md.

STEP 2 — Inject protocol block into CLAUDE.md
- Insert the Task Tracking Protocol block (from the upgrade kit) into
  CLAUDE.md. Place it before the final section (before "## 环境").
- The block starts with "## Task Tracking Protocol (mandatory)" and ends
  at the end of the Bootstrapping section.
- Do NOT modify any existing content. Only append the new block.

STEP 3 — Create .claude/current_task.md
- Using the metadata extracted in Step 1, populate the template:
  - Task Index: main = "Project active development", status = main,
    tickets = [], converge = "—"
  - Project Snapshot: fill from extracted metadata
  - Handoff Blob: synthesize from Snapshot (≤200 words)
- Write to .claude/current_task.md.

STEP 4 — Verify
- Re-read CLAUDE.md and confirm the protocol block is present and unmodified.
- Re-read .claude/current_task.md and confirm all sections are populated.
- Report:
  "Harness upgrade complete.
   - Protocol injected: <N> lines added to CLAUDE.md
   - Task state file: .claude/current_task.md created (<N> lines)
   - Next step: ask user 'What is the current main task?' to align Task Index"
```

---

## Cross-Project Portability Notes

- **Protocol is self-contained**: 仅依赖文件 I/O，不依赖任何项目特定的工具/库/API
- **Project Snapshot source**: ENGINEERING_INDEX.md > CLAUDE.md > 人工输入 (fallback chain)
- **Handoff Blob 长度**: ~200 words, 适合放入 Agent prompt 开头
- **文件数**: 仅需 2 个文件 (CLAUDE.md 新增 1 block + `.claude/current_task.md`)
- **零破坏性**: 只追加内容到 CLAUDE.md，不修改现有内容