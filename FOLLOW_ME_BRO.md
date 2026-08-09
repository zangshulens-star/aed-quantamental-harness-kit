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

1. Run `python --version`. You need **Python >= 3.10**.
   - If missing or too old: on Windows try `py -3.13 --version`, `py -3.12 --version`, `py -3.11 --version` (or `python3.13` / `python3.12` / `python3.11` on Mac/Linux). Whichever works becomes your `PYTHON` for every command below (e.g. `py -3.13` instead of `python`).
   - If none works: STOP and tell the user: "You need Python 3.10 or newer. Go to python.org, download the installer, run it, and **tick the box 'Add Python to PATH'**. Then come back and ask me again." (中文：你需要 Python 3.10 或更新版本。去 python.org 下载安装包，安装时**一定要勾选 "Add Python to PATH"**，装完再来找我。)
2. Run `PYTHON -m pip --version` (using your `PYTHON` from step 1). If missing, run `PYTHON -m ensurepip` then retry.
   - **Always use `PYTHON -m pip`, never bare `pip`.** On machines with multiple Python versions, bare `pip` often belongs to a different interpreter than `python` — packages land in one Python while scripts run on another, and verification fails with `ModuleNotFoundError`.
3. Report: "Python found, version X. Starting installation."

## Phase 1 — quant-defence (CLI toolbelt)

1. `python -m pip install -e ./quant-defence` (use your `PYTHON` from Phase 0)
2. Verify: run `qh-verify --help` — should print usage without error.
   - Fallback: if `qh-verify` is not found, retry the install once; if the command is still missing, locate the Scripts/bin directory printed by pip and use the full path.
3. Report: "quant-defence installed. You now have qh-verify / qh-null-audit / qh-coverage commands." (中文：装好了量化防守工具带。)

## Phase 2 — eco-harness (open data layer)

1. `python -m pip install -r ./eco_harness/requirements.txt` (use your `PYTHON` from Phase 0)
2. Verify: run `python -c "from eco_harness import EcoHarness; print('EcoHarness OK')"` from the kit root — expect `EcoHarness OK`.
   - If this fails with `ModuleNotFoundError` for a package pip just installed: you are hitting the multi-Python trap — re-run step 1 with the exact same `PYTHON` you use in this verify command, then retry.
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

## Phase 5 — After installation (mandatory, do not skip)

Installation is not the finish line. Do ALL THREE of the following, in plain words, both languages where marked:

**1. Explain what each piece is FOR and when the user would touch it:**

- **quant-defence**: when you have a research paper or numbers to check — the `qh-*` commands verify claims, hunt NaN degradation, check look-ahead bias. You don't touch it until you have something to verify.
- **eco-harness**: your data layer. When you need macro/financial data, ask your agent "pull X from eco-harness" — one-line calls, 20+ sources. Three sources need free API keys (FRED / EIA / UN Comtrade); everything else works now.
- **task-tracking-protocol**: only matters INSIDE a real project — it gives the AI memory across sessions in that project. Installing it here was just practice.
- **The other two context-governance pieces need no install**: handoff-blob is already Section 3 of the protocol (sub-agent handoffs); index-chaptered-docs is a set of templates you copy into a project's `docs/` folder once its documentation grows. (中文：另外两个不用装——交接块已经含在协议里了；分章文档是模板，项目文档变多时再拷。)

**2. Ask the user (this question is mandatory):**

> "Everything is installed — but a harness only earns its keep inside a real project. Do you have something you want to build? If yes, tell me what it is, and I'll walk you through: (1) create or open the project folder, (2) initialize its memory file (CLAUDE.md) if it doesn't have one, (3) install the Task Tracking Protocol into it, and (4) design the architecture with you BEFORE writing any code. (中文：东西都装好了，但工具带要装在真项目里才有用。你想做点什么吗？告诉我你的想法，我带你走四步：建/开项目文件夹 → 没有记忆文件就先建 CLAUDE.md → 把任务追踪协议装进去 → **先一起做架构设计，再写代码**。)"

**3. If the user names a project: do those four steps with them, starting with architecture design, not code.** The methodology this kit came from is design-first: a one-person desk outperforms a team when the architecture is decided up front and the harness keeps every session honest to it. Do not let the user skip the design conversation.
