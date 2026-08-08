# FOLLOW_ME_BRO.md — Zero-Code Installation

**For humans**: You don't need to know how to code. Open your AI coding tool (Claude Code / Kimi Code / Cursor), make sure this folder is your current workspace, and paste this sentence:

> Read FOLLOW_ME_BRO.md and do exactly what it says, step by step, until done.

That's it. The agent will install everything and tell you in plain words what worked.

**给人看的**：不需要会编程。打开你的 AI 编程工具（Claude Code / Kimi Code / Cursor），把这个文件夹设为工作目录，然后贴这句话：

> 读 FOLLOW_ME_BRO.md，按里面的步骤一步一步做完。

剩下的 agent 会全部搞定，用大白话告诉你装好了什么。

---
---

# AGENT INSTRUCTIONS — EXECUTE BELOW

You are an installation agent for a user who **cannot code**. Your job: install all three components of this kit, verify each, and report in plain, friendly language. Follow every step literally. Do not skip verification. If something fails, try the fallback, and if it still fails, report it clearly and move to the next component — never leave the user with a half-explained mess.

## Phase 0 — Environment check

1. Run `python --version` (or `python3 --version`).
   - If missing: STOP and tell the user: "You need Python first. Go to python.org, download the installer, run it, and **tick the box 'Add Python to PATH'**. Then come back and ask me again." (中文：你需要先装 Python。去 python.org 下载安装包，安装时**一定要勾选 "Add Python to PATH"**，装完再来找我。)
2. Run `pip --version` (or `pip3 --version`). If missing, run `python -m ensurepip` then retry.
3. Report: "Python found, version X. Starting installation."

## Phase 1 — quant-defence (CLI toolbelt)

1. `pip install -e ./quant-defence`
2. Verify: run `qh-verify --help` — should print usage without error.
   - Fallback: try `python -m pip install -e ./quant-defence`; if the pip cache/network fails, retry once.
3. Report: "quant-defence installed. You now have qh-verify / qh-null-audit / qh-coverage commands." (中文：装好了量化防守工具带。)

## Phase 2 — eco-harness (open data layer)

1. `pip install -r ./eco-harness/requirements.txt`
2. Verify: run `python -c "import sys, importlib; sys.path.insert(0,'.'); importlib.import_module('eco-harness'); print('EcoHarness OK')"` — expect `EcoHarness OK`. (The folder name `eco-harness` contains a hyphen, so the package must be imported via `importlib` rather than a plain `import` statement.)
   - Fallback: `python -m pip install -r ./eco-harness/requirements.txt`.
3. Optional keys (do NOT block on these): tell the user three sources need a free API key — FRED (fred.stlouisfed.org), EIA (eia.gov/opendata), UN Comtrade (comtradeplus.un.org) — and that everything else works without keys.
4. Report: "eco-harness installed. 20+ open data sources are one-line calls away." (中文：数据基座装好了。)

## Phase 3 — task-tracking-protocol (only if the user wants it in THIS project)

1. Ask the user (plain words): "Do you want me to install the Task Tracking Protocol into this project? It helps AI remember where work stopped between sessions. (中文：要不要把任务追踪协议装进这个项目？它让 AI 每次醒来都知道上次干到哪。)"
2. If yes: open `context-governance/task-tracking-protocol/UPGRADE_KIT.md` and follow its Agentic Self-Execution Prompt exactly, including its verification step.
3. If no: skip.

## Phase 4 — Final report (plain language, both languages)

Tell the user, in this shape:

```
Installation complete:
✅ / ❌ quant-defence (CLI tools)
✅ / ❌ eco-harness (open data, 20+ sources)
✅ / ➖ task-tracking-protocol (installed / skipped)
✅ / ⚠️ anything failed → what to do about it, in one sentence.

装完了：上面打勾的就是能用的。有问题的那行后面写了怎么办。
```

Rules: never invent success — every ✅ must come from a verification command that actually passed. Keep all user-facing text short and friendly. No jargon.
