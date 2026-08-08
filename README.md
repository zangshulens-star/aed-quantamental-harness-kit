# AED Quantamental Harness Kit

> **AED = AI-Empowered Desk.** One person's desk, running on AI — the kit that lets a single operator run what used to take a team.

## Why this kit exists

Two convictions, learned from building production systems with AI — the first system started seven months ago, and the heavy ones (research pipeline, quant platform, this harness) were all built in the last three:

1. **Tokenomics.** You don't need the most expensive model to get top-tier development results. A hand-tuned harness — task tracking, document governance, verification layers, cost-disciplined prompting — lets a cheap Chinese open-source LLM API running inside your coding agent produce results that approach frontier-model output. The entire system this kit was extracted from cost **$720 in total API spend**. The model is a filter; the harness is the intelligence multiplier.

2. **Data democratization.** Serious quantamental research shouldn't require a Wind or Bloomberg terminal. The open data ecosystem — FRED, World Bank, IMF, BIS, OECD, central banks, multilateral databases — already covers most of what macro and credit research needs. What's missing isn't access; it's a clean way to use it. This kit's EcoHarness module unifies 20+ open sources behind one-line calls.

This kit is the methodology layer extracted from a working production system: four production applications, ~330K lines of code, 21 agents, built by one operator with AI as the engineering team. It is not a framework to install and configure. It is a set of protocols and tools that keep multi-agent work **coherent, auditable, and transferable** as it scales.

---

## What's inside

```
aed_quantamental_harness_kit/
├── context-governance/
│   ├── task-tracking-protocol/     ← Multi-session task continuity (self-installing Upgrade Kit)
│   ├── index-chaptered-docs/       ← Documentation governance spec + templates for agentic projects
│   ├── handoff-blob/               ← Sub-agent context injection spec (~200-word fixed format)
│   └── memo-harness/               ← Per-round conversation archive protocol (memo/ directory)
├── quant-defence/                  ← Quant research defence toolbelt (pip-installable CLI suite)
└── eco-harness/                    ← 20+ open data sources, one-line calls
```

### context-governance / task-tracking-protocol

**Solves: state loss across multi-turn, multi-branch, multi-agent work.**

LLM sessions get compressed, agents get swapped, parallel tasks branch. Without a protocol, every new session guesses "where did we get to?" TTP defines startup recovery, branch management (main/branched, no silent switching), agent handoff, and state persistence — via two files (a CLAUDE.md protocol block + `.claude/current_task.md`). **The Upgrade Kit is a single prompt** — hand it to any Claude Code agent and it self-installs: audit, inject, initialize, verify.

- `TASK_TRACKING_PROTOCOL.md` — full protocol spec
- `UPGRADE_KIT.md` — self-installing kit (agentic self-execution prompt + current_task.md template)

### context-governance / index-chaptered-docs

**Solves: documentation systems decaying as projects grow.**

A three-layer structure (master index / architecture / chapter docs) built against three real failure modes: compression amnesia (context lost after compaction), doc rot (docs decay until nobody trusts them), and agents reading the wrong file. Design specs are "edit in place, never append"; progress logs are "append-only, keep history" — both decay channels sealed.

- `SPEC.md` — structure, mandatory reading protocol, writing rules
- `templates/` — three ready-to-use templates

### context-governance / handoff-blob

**Solves: sub-agents starting with zero context.**

A fixed-format text block of ≤200 words (project identity + current task state + recent milestone + key files), prepended verbatim to any sub-agent prompt. Constant transfer cost, machine-checkable format, derived from the task state file (never hand-edited).

- `SPEC.md` — format, generation rules, discipline (no sensitive info)

### context-governance / memo-harness

**Solves: process knowledge evaporating — task state survives, but the "why" doesn't.**

TTP's state file answers "what now"; it says nothing about "how did we get here" — rejected options, past constraints, the reasoning behind decisions. Memo Harness is the archive layer: at the end of every conversation round, the agent must ask "Run memo harness?"; on yes, the round is written to `memo/memo_<summary_title>_<yyyymmdd>.md` — append-only, never overwritten, never written silently.

- `SPEC.md` — turn-end ritual, naming convention, memo template, division of labor with TTP, injectable CLAUDE.md block

### quant-defence

**Solves: nobody checks whether the numbers in quant research are actually right.**

A pip-installable CLI toolbelt that adds a verification layer to quantitative research: claims verification (can every number in the paper be recomputed from data/engine?), NaN-degradation audit, paper-claims coverage, look-ahead bias checks, parameter sensitivity, rolling regression. Zero-config. Dependencies: pandas / numpy / pyyaml.

```bash
pip install -e ./quant-defence
qh-verify --claims validation/claims.yaml --all
qh-null-audit --panel data/panel.csv
qh-coverage --paper paper/ --claims validation/claims.yaml
```

### eco-harness

**Solves: open macro/financial data is rich but unusable — every source has its own API, format, and quirks.**

20+ open data sources unified behind one-line calls:

```python
from eco_harness import EcoHarness
eh = EcoHarness(fred_api_key='YOUR_KEY')
eh.us.gdp()          # FRED
eh.cn.cpi()          # AKShare / PBoC / NBS
eh.global_.gdp('CHN')  # World Bank / IMF / OECD via SDMX
```

**Sources included** (all open/public): FRED · AKShare (China A-shares & macro) · PBoC · National Bureau of Statistics of China · World Bank · IMF DOT · IMF COFER · BIS · OECD/SDMX · ECB · Eurostat · BoJ · EIA · UN Comtrade · GDELT · UCDP · SIPRI · OpenSanctions · OFAC · UN Voting · IPU · WGI · CBO · GSDB · yfinance.

**Three sources require a free API key** (register once, set env var or pass to constructor):

| Source | Get a key (free) | Env var |
|--------|------------------|---------|
| FRED | https://fred.stlouisfed.org → "My Account" → API Keys | `fred_api_key` (constructor) |
| EIA | https://www.eia.gov/opendata/ → Register | `eia_api_key` (constructor) |
| UN Comtrade | https://comtradeplus.un.org → Sign up → API key | `UNCOMTRADE_API_KEY` |

Optional: `tavily-python` (web search) is supported but not bundled — `pip install tavily-python` and register at https://tavily.com if needed.

Install: `cd eco-harness && pip install -r requirements.txt` (or run `python install.py` for guided setup).

---

## Where this fits

| Tool | What it governs |
|------|-----------------|
| Spec-Kit-style | **Specs** — where requirements come from |
| Memory-Bank-style | **Memory** — what a single agent remembers across sessions |
| **This kit** | **Multi-agent discipline** — handoffs, branch convergence, output audit |

No conflict. This kit assumes you already have a coding agent; it keeps **a team of agents (or one agent's hundred sessions) from making a mess**.

---

## Production evidence

Every component here was extracted from a live production environment, not written for open source:

- **Scale**: four production systems, ~330K LOC, 21 agents, 1,000+ entity coverage running daily
- **Cost**: $720 total LLM API spend for all of it
- **Transferability proof**: the task tracking protocol is maintained daily by a colleague with zero coding background — the methodology's first human-to-human transfer
- **Governance in production**: docs-before-code constitution, provenance registry (agents propose, humans approve), disk-truth auditing — all enforced daily

---

## Getting started

**Prerequisite — give your project a memory first.** The harness installs *into* your project's memory files: the task-tracking protocol injects a block into your `CLAUDE.md` and keeps its state in `.claude/current_task.md`. If the project you want to upgrade doesn't have a `CLAUDE.md` yet, create one first — open Claude Code in that project and run `/init`, or ask any coding agent to "write a CLAUDE.md for this project". Without it, the protocols have nothing to attach to. (前置条件：先给项目建好记忆文件。harness 是装进项目的 `CLAUDE.md` 和 `.claude/` 里的——没有的话先在项目里跑 Claude Code 的 `/init`，或让任意 agent 给项目写一个 CLAUDE.md，否则协议无处附着。)

**Zero-code install**: open your AI coding tool in this folder and paste one sentence — `Read FOLLOW_ME_BRO.md and do exactly what it says` — the agent installs and verifies everything for you. (零代码安装：在 AI 编程工具里打开本文件夹，贴一句"读 FOLLOW_ME_BRO.md 照着做"，agent 会装好并验证全部组件。)

**Manual install** (if you prefer):

**context-governance**: copy the protocol files you need, or hand the Upgrade Kit prompt to your agent:

```
Install the Task Tracking Protocol into this project by following
aed_quantamental_harness_kit/context-governance/task-tracking-protocol/UPGRADE_KIT.md
step by step. Do not skip verification.
```

**quant-defence**: `pip install -e ./quant-defence` → `qh-*` commands available.

**eco-harness**: `pip install -r requirements.txt` in `eco-harness/` → `from eco_harness import EcoHarness`.

---

## Recommended tooling

The kit is agent-agnostic, but this is the setup it was built and battle-tested with:

- **Editor**: VS Code
- **Coding agents**: the Kimi Code and Claude Code extensions, running side by side in the same editor
- **Model pairing** (the tokenomics play):
  - **Kimi K3** — architecture and audit passes: system design, doc governance, cross-file consistency review, final-gate checks
  - **DeepSeek V4 Pro** — the main coding bot, configured inside Claude Code; near-frontier output at open-source API prices

The split is deliberate. A cost-disciplined workhorse model writes the code; a second model from a different family audits it with fresh eyes. That cross-check — not an expensive model — is how $720 of total API spend produced ~330K lines of production code. Configure both, route by task type, and let the harness keep the two agents coherent.

---

## 中文附注（模块功能与安装概要）

- **task-tracking-protocol（任务追踪协议）**：解决多会话/多分支/多代理协作中的状态丢失。安装：把 `UPGRADE_KIT.md` 里的自执行 prompt 发给你的 agent，它自动完成安装与验证。
- **index-chaptered-docs（分章文档系统）**：主索引 + 架构 + 章节三层结构，专治文档腐化和 agent 读错文件。模板在 `templates/` 直接用。
- **handoff-blob（交接块）**：≤200 词固定格式，spawn 子代理时前置到 prompt，解决子代理零上下文启动。
- **memo-harness（逐轮存档协议）**：每轮对话结束必须问"要不要存档"，yes 则写入 `memo/memo_<概要标题>_<yyyymmdd>.md`，只追加不覆写。TTP 管"现在在哪"，memo 管"怎么走到这的"。
- **quant-defence（量化防守工具带）**：`pip install -e ./quant-defence`，之后 `qh-verify` / `qh-null-audit` / `qh-coverage` 命令可用。
- **eco-harness（开源数据基座）**：20+ 公开数据源一行调用。`cd eco-harness && pip install -r requirements.txt`。FRED / EIA / UN Comtrade 需免费注册 API key（链接见上表），其余源开箱即用。
- **推荐工具配置**：VS Code + Kimi Code / Claude Code 双扩展。模型搭配：Kimi K3 负责架构与审计，DeepSeek V4 Pro（配在 Claude Code 里）作为主力编码模型——便宜模型写码、异家模型复核，这就是 $720 总 API 花费跑出 33 万行生产代码的核心打法。

---

## Disclaimer

**This is a reference implementation shared as-is. It is archived, not actively maintained.** Issues and PRs may not be answered. The protocols are the product; the code is evidence that they work. Use them, fork them, rewrite them in your own stack — that is the point.

## License

MIT — see [LICENSE](LICENSE).
