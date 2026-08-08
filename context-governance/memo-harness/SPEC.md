# Memo Harness — 规范

> 逐轮对话的记忆存档协议：每轮对话结束，agent 必须询问用户是否归档本轮内容；用户同意则写入 `memo/` 目录下的一篇 markdown memo。
> 与 Task Tracking Protocol 配套使用（TTP 管"现在在哪"，Memo Harness 管"怎么走到这的"）。

---

## 1. 为什么需要它

TTP 的 `current_task.md` 是**当前状态**——它永远只反映最新任务态，旧状态被覆写。但项目真正值钱的往往是过程：为什么这么决策、哪个方案被否过、当时的约束是什么。这些在状态覆写和会话压缩中全部丢失。

Memo Harness 补上这一层：**每一轮对话是一篇不可覆写的存档**。`current_task.md` 回答"现在该干什么"，memo/ 回答"我们是怎么走到这的"。

---

## 2. 协议规则

### 2.1 目录（强制）

- 项目根目录必须有 `memo/` 目录。首次运行时不存在则创建
- memo 文件**只进不出**：只追加新文件，永不修改、永不删除历史 memo

### 2.2 轮末仪式（强制）

- 每轮对话结束前，agent **必须**询问用户：
  > "Run memo harness?（要不要把本轮内容存档进 memo？）"
- 用户说 **yes** → 写 memo（见 §3、§4）
- 用户说 **no** → 跳过。**禁止静默写入，也禁止忘记询问**

### 2.3 文件命名范式

```
memo_<对话内容概要标题>_<yyyymmdd>.md
```

- `概要标题`：本轮主题的小写 snake_case 短 slug（3-6 词），如 `fix_dotenv_multipython`、`phase4_release_discussion`
- `yyyymmdd`：本地日期，如 `20260808`
- 同一天同主题第二篇：追加序号 `_2`、`_3`，如 `memo_release_discussion_20260808_2.md`

示例：`memo_fix_dotenv_multipython_20260808.md`

### 2.4 memo 内容模板

```markdown
# Memo: <概要标题>
> Date: <yyyy-mm-dd> | Project: <项目名>

## 本轮做了什么
<3-8 条要点：完成的事、跑过的验证、改动的文件>

## 关键决策
<每条决策一行：决定了什么 + 为什么>

## 遗留问题
<没解决的、被推迟的、待用户拍板的>

## 下一步
<下一轮最该先做的 1-3 件事>
```

**硬约束**：
- 一篇 memo 只记一轮——跨轮内容拆多篇
- 写事实，不写流水账：决策和遗留比过程重要
- 敏感信息（凭证、密钥、内部路径、人名）不得进 memo——它是长期存档，传播面不可控

---

## 3. 安装（CLAUDE.md 协议块）

把以下 block 注入目标项目的 `CLAUDE.md`（可紧跟 TTP 协议块之后）：

````markdown
## Memo Harness (mandatory)

### 1. Setup
- Ensure `memo/` exists at project root; create if missing.
- **One round = one new memo file.** NEVER append to an existing memo; NEVER modify or delete historical memos. Each conversation round gets its own standalone file.

### 2. Turn-end ritual
- Before ending every conversation round, MUST ask the user: "Run memo harness?"
- If yes: write `memo/memo_<summary_title>_<yyyymmdd>.md`
  - summary_title: 3-6 word lowercase snake_case slug of this round's topic
  - Same topic, same day: append `_2`, `_3`, ...
  - Content per the template in context-governance/memo-harness/SPEC.md §2.4:
    what was done / key decisions / open questions / next steps
- If no: skip. NEVER write silently, NEVER forget to ask.

### 3. Division of labor with TTP
- `.claude/current_task.md` = current state (overwritten as tasks evolve)
- `memo/` = permanent narrative archive (one file per round, never overwritten)
- State change → update current_task.md immediately; round end → offer memo.
````

---

## 4. 与 TTP 的分工

| | TTP (`current_task.md`) | Memo Harness (`memo/`) |
|---|---|---|
| 回答的问题 | 现在该干什么 | 怎么走到这的 |
| 写入时机 | 状态变化即写（静默、强制） | 轮末询问后写（用户批准） |
| 生命周期 | 持续覆写 | 只追加，永不覆写 |
| 读者 | 下一轮/下一个 agent | 未来的你和审计者 |

两者接合点：memo 的"下一步"应与 `current_task.md` 的 Task Index 保持一致；写 memo 时如发现状态漂移，先更新 current_task.md。

---

## 5. 示例

`memo_phase4_release_discussion_20260808.md`：

```markdown
# Memo: phase4_release_discussion
> Date: 2026-08-08 | Project: aed_tooling

## 本轮做了什么
- 私有 repo 推送成功（61 文件，main 分支），topics 四项设置完成
- demo 测试通过：新 agent 按 FOLLOW_ME_BRO 装通全部三组件
- demo 暴露多 Python 陷阱（python→3.7 / pip→3.13），已加固 FOLLOW_ME_BRO 三处

## 关键决策
- 发布流程改为"先私有、demo 验证、再转公开"——比直接 --public 多一道真人验收
- FOLLOW_ME_BRO 全文禁用裸 pip，强制 `PYTHON -m pip`

## 遗留问题
- eco-harness/skill.md 约 30 处 `from bundle.*` 旧写法待处置（倾向原样保留+README 加导入说明）

## 下一步
- commit 加固改动 → 转 public → Phase 5 clone 验证汇报
```
