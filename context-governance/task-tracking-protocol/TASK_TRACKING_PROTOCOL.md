# Task Tracking Protocol v1.0

> **Scope**: Project-neutral agent harness for Claude Code multi-turn task continuity.
> **Compatible**: Any project with CLAUDE.md + ENGINEERING_INDEX.md (or equivalent root doc).
> **Dependencies**: None. Self-contained file I/O protocol.

---

## Problem Statement

1. **Compression amnesia**: Claude Code compresses old messages → agent forgets task context → hallucinates
2. **Branch divergence**: Sub-tasks fork off mainline → no mechanism to converge back
3. **Agent handoff discontinuity**: New sub-agent spawns with zero context → repeats discovery work

## Solution Architecture

```
CLAUDE.md (compression-proof, system prompt)
  └─ "Task Tracking Protocol" rules → mandatory read/write cycle every turn

.claude/current_task.md (≤80 lines, task state file)
  ├─ Project Snapshot  (static, generated once)
  ├─ Task Index         (dynamic, updated every turn)
  └─ Handoff Blob       (auto-synthesized from above two)
```

## Mechanism

### 1. Compression Recovery Loop

```
Compression drops old turns
  → New turn starts
  → CLAUDE.md rule triggers: "Read .claude/current_task.md"
  → Fresh file read restores full task state
  → LLM continues from exact checkpoint
```

File read is a single tool call, ~80 lines, negligible context cost. Recovery is instantaneous because `current_task.md` is always up-to-date (written at end of previous turn).

### 2. Branch-Converge Protocol

```
Main task running
  → Sub-task identified → append ticket to Task Index, status: branched
  → Sub-task completed → mark ticket [x], ASK USER: "Close ticket and converge to main?"
  → User "yes" → update converge pointer, status: main
  → User "no"  → keep branched, continue next sub-task
```

The ASK is mandatory — LLM cannot silently switch back. This is enforced by the protocol rules in CLAUDE.md.

### 3. Agent Handoff via Handoff Blob

```
Parent LLM about to spawn Agent
  → Read .claude/current_task.md
  → Extract Handoff Blob section
  → Prepend to Agent prompt: "[HANDOFF BLOB]\n{blob}\n[/HANDOFF BLOB]\n\nSpecific task: ..."
  → Agent receives full project context + current task state
```

The blob contains:
- Project identity (name, purpose, tech stack)
- Current mainline task
- Active tickets and their status
- Key file paths (architecture, chapters, data)
- Latest completion milestone

~200 words. Agent doesn't need conversation history.

---

## File Format

### .claude/current_task.md

```markdown
# Task Index

main:     <one-line description of main trunk task>
status:   main | branched
tickets:
  T01 - [x] <ticket title>  → completed YYYY-MM-DD
  T02 - [ ] <ticket title>  → in_progress
converge: <T02 close → 回归 <main task>>

---

## Project Snapshot
> Generated: YYYY-MM-DD | Source: docs/ENGINEERING_INDEX.md

### Identity
<project name> — <one-line description>

### Architecture
<3-5 bullets: tech stack, agent count, key directories, data root>

### Key Paths
- Main index: <path>
- Architecture: <path>
- Agent root: <path>
- Data: <path>
- Memo: <path>

---

## Handoff Blob
> Auto-generated at agent spawn time from Snapshot + Task Index.
> Copy everything below to Agent prompt.

[HANDOFF]
Project: <project name>
About: <one-line description>
Stack: <tech stack summary>
Main task: <current mainline task>
Status: <main | branched, active ticket: T0X>
Done: <last 2-3 completed tickets>
Key files: <3-5 critical paths>
[/HANDOFF]
```

---

## CLAUDE.md Integration Block

Insert this block into any project's CLAUDE.md (end of file, before environment section):

```markdown
## Task Tracking Protocol (mandatory)

### 1. Startup Recovery
- Every turn start: Read `.claude/current_task.md`
- If file missing: Initialize from project metadata

### 2. Branch Management
- New sub-task: append ticket, set status: branched
- Sub-task complete: mark [x], ask user "Close ticket → converge to main?"
- User confirms: update converge pointer, set status: main
- NEVER silently switch between main and branched

### 3. Agent Handoff
- Before Agent tool call:
  a) Read `.claude/current_task.md`
  b) Prepend Handoff Blob to Agent prompt
  c) Follow with specific task instruction
- Agent prompt format:
  ```
  [HANDOFF]
  {Handoff Blob section verbatim}
  [/HANDOFF]

  Specific task: {detailed instruction}
  ```

### 4. State Persistence
- Task status change → write `.claude/current_task.md` immediately
- Turn end → verify file reflects latest state
- Project Snapshot → update on major milestones (phase complete, new agent added)
```

---

## Bootstrapping: First-Time Initialization

When `.claude/current_task.md` does not exist:

```
Step 1: Read docs/ENGINEERING_INDEX.md (or CLAUDE.md if no index exists)
Step 2: Extract project identity, tech stack, key paths
Step 3: Initialize Task Index (main = user's first request, status = main, tickets = [])
Step 4: Generate Project Snapshot from extracted metadata
Step 5: Write .claude/current_task.md
Step 6: Report to user: "Task tracking initialized. Current main: <X>"
```

---

## Compatibility Matrix

| Project has | Handoff Blob source | Fallback |
|------------|-------------------|----------|
| ENGINEERING_INDEX.md | Read §1+§4 | — |
| CLAUDE.md only | Read §1 + directory structure | — |
| Neither | Ask user for 3-sentence project summary | Manual init |